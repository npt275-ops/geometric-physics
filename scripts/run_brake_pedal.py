"""Bài chuẩn BÀN ĐẠP PHANH — chạy trên laptop người vận hành (tầng 2.3).

Chạy CẢ HAI: multi (3 case) và single (đối chứng) với checkpoint riêng —
ngắt lúc nào cũng được, chạy lại là tiếp tục. Xong tự đánh giá chéo:

  DoD-2.1: c₃(ρ_single)/c₃(ρ_multi) ≥ 1.3  (tải ngang đạp xéo — spec 4b)
  DoD-2.2: STL watertight, 1 khối          DoD-2.4: volume 45% ±1%

Bằng chứng vào bench/: report JSON, STL, render PNG, viewer HTML.
"""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from geophys.export_stl import export_stl  # noqa: E402
from geophys.fea3d import FEA3D  # noqa: E402
from geophys.grid3d import Grid3D  # noqa: E402
from geophys.optimize3d import optimize3d  # noqa: E402
from geophys.render3d import SnapshotRecorder3D, render_isosurface  # noqa: E402
from geophys.spec3d import load_spec3d  # noqa: E402

BENCH = ROOT / "bench"


def run_one(tag, spec_name):
    spec = load_spec3d(ROOT / "examples" / spec_name)
    ck = BENCH / f"brake_{tag}_checkpoint.npz"
    t0 = time.perf_counter()

    def progress(i, rho, c):
        if i % 5 == 0 or i == 1:
            print(f"  [{tag}] vòng {i:3d} · c={c:.1f} · "
                  f"{time.perf_counter() - t0:5.0f}s", flush=True)

    res = optimize3d(spec, max_iter=200, method="cg", callback=progress,
                     checkpoint_path=ck, checkpoint_every=5,
                     log_path=BENCH / f"brake_{tag}_log.json",
                     resume=ck.is_file())
    print(f"  [{tag}] {'HỘI TỤ' if res.converged else 'CHƯA hội tụ'} "
          f"sau {res.n_iter} vòng, c={res.compliance:.2f}", flush=True)
    return spec, res


def main() -> int:
    BENCH.mkdir(exist_ok=True)
    print("[brake] Bài chuẩn 80×40×10 (32k phần tử) × 2 lượt chạy — "
          "checkpoint mỗi 5 vòng, ngắt được.", flush=True)
    spec_m, res_m = run_one("multi", "spec_brake_pedal.json")
    spec_s, res_s = run_one("single", "spec_brake_pedal_single.json")

    fea = FEA3D(spec_m, Grid3D(spec_m))
    def cross(rho, ci):
        f = fea.forces[ci]
        return fea.compliance(fea.solve(rho, 3.0, force=f), force=f)
    c2_s, c2_m = cross(res_s.rho, 1), cross(res_m.rho, 1)
    c3_s, c3_m = cross(res_s.rho, 2), cross(res_m.rho, 2)
    ratio_side = c3_s / c3_m

    stl_path, rep = export_stl(res_m.rho, ROOT / "media" / "brake_pedal.stl")
    render_isosurface(res_m.rho, ROOT / "media" / "brake_pedal_iso.png")
    rec = SnapshotRecorder3D(every=1)
    rec.add_final(res_m.n_iter, res_m.rho, res_m.compliance)
    rec.to_html(ROOT / "media" / "brake_pedal_viewer.html",
                title="ban dap phanh nhom 6061 — 3 load case")

    dod21 = res_m.converged and res_s.converged and ratio_side >= 1.3
    dod22 = rep["watertight"] and rep["n_components"] == 1
    dod24 = abs(float(res_m.rho.mean()) - 0.45) < 0.0045
    report = {
        "multi": {"n_iter": res_m.n_iter, "converged": res_m.converged,
                  "c_weighted": round(res_m.compliance, 3)},
        "single": {"n_iter": res_s.n_iter, "converged": res_s.converged,
                   "c": round(res_s.compliance, 3)},
        "cross_eval": {
            "c2_lech15_single": round(c2_s, 2),
            "c2_lech15_multi": round(c2_m, 2),
            "c3_ngang_single": round(c3_s, 2),
            "c3_ngang_multi": round(c3_m, 2),
            "ty_so_DoD21_c3": round(ratio_side, 3),
        },
        "volume_multi": round(float(res_m.rho.mean()), 5),
        "stl": rep,
        "DoD-2.1": "PASS" if dod21 else "FAIL",
        "DoD-2.2": "PASS" if dod22 else "FAIL",
        "DoD-2.4": "PASS" if dod24 else "FAIL",
    }
    out = BENCH / "report_brake_pedal.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print("\n===== KẾT QUẢ =====")
    for k in ("cross_eval", "volume_multi", "DoD-2.1", "DoD-2.2", "DoD-2.4"):
        print(" ", k, ":", report[k])
    print("Report:", out)
    print("STL:", stl_path, "| render + viewer trong media/")
    ok = dod21 and dod22 and dod24
    print("KET QUA:", "3/3 DoD PASS — bao agent kem so lieu"
          if ok else "co DoD FAIL — gui report cho agent")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
