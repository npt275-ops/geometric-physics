"""Vòng lặp tối ưu topology — nối 4 module STABLE thành pipeline hoàn chỉnh.

solve → ∂c/∂ρ → filter → OC → kiểm hội tụ (max|Δρ| < tol), lặp.
Engine headless: không import render; móc nối ngoài qua callback.
converged=False là kết quả TƯỜNG MINH — không bao giờ nuốt.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from geophys.fea2d import FEA2D
from geophys.filter2d import SensitivityFilter
from geophys.grid2d import Grid2D
from geophys.oc_update import oc_update
from geophys.sensitivity import dc_drho, dv_drho
from geophys.spec_loader import Spec

_LOG_EVERY = 10


@dataclass
class OptimizeResult:
    rho: np.ndarray          # (nelx, nely) ∈ [0, 1]
    compliance: float        # c cuối cùng
    n_iter: int              # số vòng đã chạy
    converged: bool          # đạt max|Δρ| < tol trước max_iter?
    history: dict = field(default_factory=dict)  # compliance/change/volume


def _write_log(log_path, history) -> None:
    Path(log_path).write_text(
        json.dumps(history, ensure_ascii=False, indent=1), encoding="utf-8")


def optimize(spec: Spec, *, max_iter: int = 200, tol: float = 0.01,
             move: float = 0.2, log_path=None,
             callback=None) -> OptimizeResult:
    """Chạy trọn vòng đời tối ưu cho một Spec 2D.

    callback(i, rho, c) gọi mỗi vòng — dùng cho render/giám sát,
    engine không biết bên kia là gì.
    """
    grid = Grid2D(spec)
    fea = FEA2D(spec, grid)
    filt = SensitivityFilter(spec.nelx, spec.nely, spec.rmin)
    dv = dv_drho(fea)

    rho = grid.rho.copy()
    history = {"compliance": [], "change": [], "volume": []}
    compliance = np.inf
    n_iter = 0
    converged = False

    for n_iter in range(1, max_iter + 1):
        u = fea.solve(rho, spec.p)
        compliance = fea.compliance(u)
        dc = dc_drho(fea, u, rho, spec.p)
        dc_filtered = filt.apply(rho, dc)
        rho_new = oc_update(rho, dc_filtered, dv, spec.volfrac,
                            grid.preserve_mask, grid.void_mask, move=move)
        change = float(np.abs(rho_new - rho).max())
        rho = rho_new

        history["compliance"].append(float(compliance))
        history["change"].append(change)
        history["volume"].append(float(rho.mean()))
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
