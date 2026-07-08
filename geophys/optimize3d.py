"""Vòng lặp tối ưu topology 3D — nối các module STABLE thành pipeline.

solve (warm start CG) → ∂c/∂ρ → filter 3D → OC (tái dùng oc_update STABLE)
→ kiểm hội tụ. Engine headless; callback là móc nối duy nhất ra ngoài.

Tầng 1.4 bổ sung (spec stage1-t4, mở khóa có nghi thức):
- checkpoint_path/checkpoint_every/resume — ngắt & chạy tiếp GIỐNG HỆT
  (mỗi vòng chỉ phụ thuộc rho + u_prev, cả hai được lưu).
- Profiling: t_solve / t_grad_filter / t_oc / rss_mb ghi vào history.
Không đổi thuật toán: không dùng tham số mới ⇒ kết quả giống bản 1.3 từng bit.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

try:
    import psutil
    _PROC = psutil.Process()
except ImportError:  # psutil khuyến nghị; thiếu thì rss_mb = -1, không chặn engine
    psutil = None
    _PROC = None

from geophys.checkpoint import load_checkpoint, save_checkpoint
from geophys.fea3d import FEA3D
from geophys.filter3d import SensitivityFilter3D
from geophys.grid3d import Grid3D
from geophys.oc_update import oc_update
from geophys.optimize import OptimizeResult
from geophys.sensitivity3d import dc_drho, dv_drho
from geophys.spec3d import Spec3D

_LOG_EVERY = 10
_HISTORY_KEYS = ("compliance", "change", "volume", "cg_iters",
                 "t_solve", "t_grad_filter", "t_oc", "rss_mb")


def _write_log(log_path, history) -> None:
    Path(log_path).write_text(
        json.dumps(history, ensure_ascii=False, indent=1), encoding="utf-8")


def _rss_mb() -> float:
    if _PROC is None:
        return -1.0
    return float(_PROC.memory_info().rss) / 1e6


def optimize3d(spec: Spec3D, *, max_iter: int = 200, tol: float = 0.01,
               move: float = 0.2, method: str = "auto", log_path=None,
               callback=None, checkpoint_path=None, checkpoint_every: int = 10,
               resume: bool = False) -> OptimizeResult:
    """Chạy trọn vòng đời tối ưu cho một Spec3D.

    resume=True: nạp checkpoint_path (digest phải khớp spec) và chạy tiếp.
    Checkpoint lưu mỗi `checkpoint_every` vòng và khi dừng (hội tụ/max_iter).
    """
    if resume and checkpoint_path is None:
        raise ValueError("resume=True cần checkpoint_path")

    grid = Grid3D(spec)
    fea = FEA3D(spec, grid)
    filt = SensitivityFilter3D(spec.nelx, spec.nely, spec.nelz, spec.rmin)
    dv = dv_drho(fea)

    rho = grid.rho.copy()
    history = {k: [] for k in _HISTORY_KEYS}
    start_iter = 0
    u_prev = None
    if resume:
        state = load_checkpoint(checkpoint_path, spec)
        rho = state["rho"]
        u_prev = state["u_prev"]
        start_iter = state["n_iter"]
        saved = state["history"]
        for k in _HISTORY_KEYS:  # tương thích checkpoint thiếu khóa mới
            history[k] = list(saved.get(k, []))

    compliance = (history["compliance"][-1]
                  if history["compliance"] else np.inf)
    n_iter = start_iter
    converged = False

    for n_iter in range(start_iter + 1, max_iter + 1):
        t0 = time.perf_counter()
        u = fea.solve(rho, spec.p, method=method, x0=u_prev)
        t1 = time.perf_counter()
        u_prev = u
        compliance = fea.compliance(u)
        dc = dc_drho(fea, u, rho, spec.p)
        dc_f = filt.apply(rho, dc)
        t2 = time.perf_counter()
        rho_new = oc_update(rho, dc_f, dv, spec.volfrac,
                            grid.preserve_mask, grid.void_mask, move=move)
        t3 = time.perf_counter()
        change = float(np.abs(rho_new - rho).max())
        rho = rho_new

        history["compliance"].append(float(compliance))
        history["change"].append(change)
        history["volume"].append(float(rho.mean()))
        history["cg_iters"].append(int(fea.last_cg_iters))
        history["t_solve"].append(t1 - t0)
        history["t_grad_filter"].append(t2 - t1)
        history["t_oc"].append(t3 - t2)
        history["rss_mb"].append(_rss_mb())

        if callback is not None:
            callback(n_iter, rho, float(compliance))
        if change < tol:
            converged = True
        if checkpoint_path is not None and (
                n_iter % checkpoint_every == 0 or converged
                or n_iter == max_iter):
            save_checkpoint(checkpoint_path, spec, rho, u_prev,
                            n_iter, history)
        if log_path is not None and (n_iter % _LOG_EVERY == 0 or converged):
            _write_log(log_path, history)
        if converged:
            break

    if log_path is not None:
        _write_log(log_path, history)
    return OptimizeResult(rho=rho, compliance=float(compliance),
                          n_iter=n_iter, converged=converged,
                          history=history)
