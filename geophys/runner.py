"""Runner — pipeline MỘT LỆNH: spec.json → STL + report (DoD-2.5).

Lớp NGOÀI engine (như render/export): được import mọi thứ; engine core
vẫn headless — guard test tầng 0.5 tiếp tục canh điều đó.
Exit code: 0 = trọn + hội tụ + STL kín · 1 = xong nhưng FAIL · 2 = spec lỗi.
"""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

import numpy as np

from geophys.checkpoint import spec_digest
from geophys.errors import SpecError
from geophys.export_stl import ExportError, export_stl
from geophys.optimize3d import optimize3d
from geophys.render3d import SnapshotRecorder3D, render_isosurface
from geophys.spec3d import load_spec3d

_TOL = 0.01


def _write_report(outdir: Path, report: dict) -> None:
    (outdir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    r = report
    md = [
        "# GP run report — " + r["spec"],
        "",
        "| Chỉ số | Giá trị |",
        "|---|---|",
        f"| Trạng thái | **{r['status']}** |",
        f"| Vật liệu | {r['material'] or 'inline'} "
        f"(yield {r['yield_mpa']} MPa) |",
        f"| Lưới | {r['grid']} · voxel {r['element_size_mm']} mm |",
        f"| Load cases | {r['n_load_cases']} |",
        f"| Hội tụ | {r['converged']} sau {r['n_iter']} vòng |",
        f"| Compliance (gia quyền) | {r['compliance']} N·mm |",
        f"| Volume fraction | {r['volume_fraction']} |",
        f"| STL | {r['stl']['path'] if r.get('stl') else 'KHÔNG XUẤT'} — "
        f"watertight={r.get('stl', {}).get('watertight')} |",
        f"| Thời gian phiên | {r['wall_s']} s |",
        f"| Spec digest | {r['digest'][:16]}… |",
        "",
        "File: " + ", ".join(r["files"]),
    ]
    (outdir / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def run_spec(spec_path, outdir=None, method: str = "auto",
             max_iter: int = 200, resume_from=None) -> tuple:
    """Chạy trọn pipeline cho một spec 3D. Trả (exit_code, report)."""
    t0 = time.perf_counter()
    spec_path = Path(spec_path)
    spec = load_spec3d(spec_path)  # SpecError lan lên cho __main__ xử

    out = Path(outdir) if outdir else Path("runs") / spec_path.stem
    out.mkdir(parents=True, exist_ok=True)
    ckpt = out / "checkpoint.npz"
    if resume_from is not None:
        src = Path(resume_from)
        if not src.is_file():
            raise SpecError("--resume-from", f"không thấy {src}", "")
        # Gauntlet bai09 16/07/2026: resume-tai-cho (src == ckpt) lam
        # copy2 no SameFileError — truong hop hop phap, chi can bo copy.
        if src.resolve() != ckpt.resolve():
            shutil.copy2(src, ckpt)

    def progress(i, rho, c):
        if i % 5 == 0 or i == 1:
            print(f"  vòng {i:3d} · c={c:.3f} · "
                  f"{time.perf_counter() - t0:5.0f}s", flush=True)

    res = optimize3d(spec, max_iter=max_iter, tol=_TOL, method=method,
                     callback=progress, checkpoint_path=ckpt,
                     checkpoint_every=5, log_path=out / "optimize_log.json",
                     resume=ckpt.is_file())
    converged = res.converged
    if (not converged and res.history["change"]
            and res.history["change"][-1] < _TOL):
        converged = True  # resume sau khi đã hội tụ — không bắt chạy lại

    stem = spec_path.stem
    files = ["checkpoint.npz", "optimize_log.json"]
    stl_report = None
    try:
        _, stl_report = export_stl(res.rho, out / f"{stem}.stl")
        files.append(f"{stem}.stl")
    except (ExportError, ValueError) as exc:
        print("[runner] STL FAIL:", exc, flush=True)
    render_isosurface(res.rho, out / f"{stem}_iso.png")
    files.append(f"{stem}_iso.png")
    rec = SnapshotRecorder3D(every=1)
    rec.add_final(res.n_iter, res.rho, res.compliance)
    rec.to_html(out / f"{stem}_viewer.html", title=stem)
    files.append(f"{stem}_viewer.html")

    ok = bool(converged and stl_report and stl_report["watertight"]
              and stl_report["n_components"] == 1)
    report = {
        "spec": str(spec_path),
        "status": "PASS" if ok else "FAIL",
        "digest": spec_digest(spec),
        "material": spec.material_name,
        "yield_mpa": spec.yield_mpa,
        "element_size_mm": spec.element_size_mm,
        "grid": f"{spec.nelx}x{spec.nely}x{spec.nelz}",
        "n_load_cases": len(spec.load_cases),
        "converged": converged,
        "n_iter": res.n_iter,
        "compliance": round(res.compliance, 4),
        "c_cases": [round(c, 4) for c in res.history["c_cases"][-1]]
        if res.history["c_cases"] else [],
        "volume_fraction": round(float(res.rho.mean()), 5),
        "stl": stl_report,
        "wall_s": round(time.perf_counter() - t0, 1),
        "files": files + ["report.json", "report.md"],
    }
    _write_report(out, report)
    print(f"[runner] {report['status']} — report: {out / 'report.md'}",
          flush=True)
    return (0 if ok else 1), report
