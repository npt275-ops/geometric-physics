"""Sensitivity Analysis — ∂c/∂ρ compliance-based (KHÔNG heuristic ứng suất).

∂c/∂ρₑ = −p·ρₑ^(p−1)·(E0 − Emin)·(uₑᵀ KE uₑ)

Compliance tự liên hợp (self-adjoint) nên công thức trên là gradient CHÍNH XÁC
— được kiểm bằng finite difference trong tests/test_sensitivity.py.
"""

from __future__ import annotations

import numpy as np

from geophys.fea2d import FEA2D


def dc_drho(fea: FEA2D, u: np.ndarray, rho: np.ndarray,
            p: float) -> np.ndarray:
    """Đạo hàm compliance theo mật độ từng element, shape (nelx, nely), ≤ 0."""
    rho = np.asarray(rho, dtype=np.float64)
    expected = (fea.grid.nelx, fea.grid.nely)
    if rho.shape != expected:
        raise ValueError(
            f"rho shape {rho.shape} — kỳ vọng {expected} (nelx, nely)")
    if u.shape != (fea.grid.n_dof,):
        raise ValueError(
            f"u shape {u.shape} — kỳ vọng ({fea.grid.n_dof},)")
    u_e = u[fea.grid.edof_mat]  # (nel, 8)
    quad = np.einsum("ij,jk,ik->i", u_e, fea.ke, u_e)  # uₑᵀ KE uₑ ≥ 0
    dc = -p * rho.ravel() ** (p - 1) * (fea.e0 - fea.e_min) * quad
    return dc.reshape(expected)


def dv_drho(fea: FEA2D) -> np.ndarray:
    """Đạo hàm thể tích theo mật độ — hằng 1 trên lưới đều."""
    return np.ones((fea.grid.nelx, fea.grid.nely), dtype=np.float64)
