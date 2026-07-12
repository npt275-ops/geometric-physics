"""Bộ đo DoD-1.2 / DoD-1.3 — CHẠY TRÊN LAPTOP CỦA NGƯỜI VẬN HÀNH.

64×32×32 (~65.536 phần tử, ~212k dof, solver CG + warm start).
Có checkpoint mỗi 5 vòng: ngắt (Ctrl+C / mất điện) → chạy lại là TIẾP TỤC.

Verdict in ra cuối cùng + ghi bench/report_64x32x32.json:
  DoD-1.2: hội tụ < 150 vòng, tổng thời gian < 3600 giây.
  DoD-1.3: peak RSS < 8192 MB.
"""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from geophys.checkpoint import load_checkpoint  # noqa: E402
from geophys.optimize3d import optimize3d  # noqa: E402
from geophys.spec3d import load_spec3d  # noqa: E402

SPEC = ROOT / "examples" / "spec3d_bench_64x32x32.json"
BENCH_DIR = ROOT / "bench"
CKPT = BENCH_DIR / "bench64_checkpoint.npz"
LOG = BENCH_DIR / "bench64_log.json"
REPORT = BENCH_DIR / "report_64x32x32.json"


def main() -> int:
    BENCH_DIR.mkdir(exist_ok=True)
    spec = load_spec3d(SPEC)
    resume = CKPT.is_file()
    if resume:
        try:
            load_checkpoint(CKPT, spec)
        except ValueError:
            print("[bench] checkpoint thuộc spec CŨ (đã đổi rmin) — chạy mới")
            try:
                CKPT.unlink()
            except PermissionError:
                # phòng hờ Windows còn khóa file: né bằng cách đổi tên
                CKPT.rename(CKPT.with_suffix(f".old_{int(time.time())}"))
            resume = False
    print(f"[bench] {'TIẾP TỤC từ checkpoint' if resume else 'chạy mới'} — "
          "64×32×32, tối đa 150 vòng, checkpoint mỗi 5 vòng")
    t0 = time.perf_counter()

    def progress(i, rho, c):
        if i % 5 == 0 or i == 1:
            print(f"  vòng {i:3d} · compliance {c:.4f} · "
                  f"{time.perf_counter() - t0:6.0f}s", flush=True)

    res = optimize3d(spec, max_iter=150, method="cg", callback=progress,
                     checkpoint_path=CKPT, checkpoint_every=5,
                     log_path=LOG, resume=resume)
    wall = time.perf_counter() - t0
    peak_mb = max(res.history["rss_mb"])
    total_solve = sum(res.history["t_solve"])

    dod12 = res.converged and res.n_iter < 150 and wall < 3600
    dod13 = 0 < peak_mb < 8192
    report = {
        "spec": SPEC.name, "n_iter": res.n_iter, "converged": res.converged,
        "compliance": res.compliance,
        "wall_s_phien_cuoi": round(wall, 1),
        "tong_t_solve_s": round(total_solve, 1),
        "peak_rss_mb": round(peak_mb, 1),
        "cg_iters_max": max(res.history["cg_iters"]),
        "DoD-1.2": "PASS" if dod12 else "FAIL",
        "DoD-1.3": "PASS" if dod13 else "FAIL",
        "ghi_chu": "wall_s là thời gian PHIÊN CUỐI; nếu có resume, cộng các phiên"
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print("\n===== KẾT QUẢ =====")
    for k, v in report.items():
        print(f"  {k}: {v}")
    print(f"\nReport: {REPORT}")
    print("Nếu 2 DoD PASS: commit thư mục bench/ làm bằng chứng, "
          "báo agent số liệu.")
    return 0 if (dod12 and dod13) else 1


if __name__ == "__main__":
    raise SystemExit(main())
