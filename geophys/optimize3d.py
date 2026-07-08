"""Vòng lặp tối ưu topology 3D — nối các module STABLE thành pipeline.

solve (warm start CG) → ∂c/∂ρ → filter 3D → OC (tái dùng oc_update STABLE
— hàm element-wise, không phụ thuộc số chiều) → kiểm hội tụ.
Engine headless; callback là móc nối duy nhất ra ngoài.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from geophys.fea3d import FEA3D
from geophys.filter3d import SensitivityFilter3D
from geophys.grid3d import Grid3D
from geophys.oc_update import oc_update
from geophys.optimize import OptimizeResult
from geophys.sensitivity3d import dc_drho, dv_drho
from geophys.spec3d import Spec3D

_LOG_EVERY = 10


def _write_log(log_path, history) -> None:
    Path(log_path).write_text(
        json.dumps(history, ensure_ascii=False, indent=1), encoding="utf-8")


def optimize3d(spec: Spec3D, *, max_iter: int = 200, tol: float = 0.01,
               move: float = 0.2, method: str = "auto", log_path=None,
               callback=None) -> OptimizeResult:
    """Chạy trọn vòng đời tối ưu cho một Spec3D.

    method truyền thẳng xuống FEA3D.solve; đường CG dùng warm start
    bằng nghiệm vòng trước (u_prev) — đo được trong history["cg_iters"].
    """
    grid = Grid3D(spec)
    fea = FEA3D(spec, grid)
    filt = SensitivityFilter3D(spec.nelx, spec.nely, spec.nelz, spec.rmin)
    dv = dv_drho(fea)

    rho = grid.rho.copy()
    history = {"compliance": [], "change": [], "volume": [], "cg_iters": []}
    compliance = np.inf
    n_iter = 0
    converged = False
    u_prev = None

    for n_iter in range(1, max_iter + 1):
        u = fea.solve(rho, spec.p, method=method, x0=u_prev)
        u_prev = u
        compliance = fea.compliance(u)
        dc = dc_drho(fea, u, rho, spec.p)
        dc_f = filt.apply(rho, dc)
        rho_new = oc_update(rho, dc_f, dv, spec.volfrac,
                            grid.preserve_mask, grid.void_mask, move=move)
        change = float(np.abs(rho_new - rho).max())
        rho = rho_new

        history["compliance"].append(float(compliance))
        history["change"].append(change)
        history["volume"].append(float(rho.mean()))
        history["cg_iters"].append(int(fea.last_cg_iters))
        if callback is not None:
            callback(n_iter, rho, float(compliance))
        if log_path is not None and n_iter % _LOG_EVERY == 0:
            _write_log(log_path, history)
        if change < tol:
            converged = True
            break

    if log_path is not None:
        _write_log(log_path, history)
    return OptimizeResult(rho=rho, compliance=float(compliance),
                          n_iter=n_iter, converged=converged,
                          history=history)
