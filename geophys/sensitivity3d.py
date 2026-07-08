"""Sensitivity Analysis 3D — ∂c/∂ρ compliance-based (KHÔNG heuristic ứng suất).

∂c/∂ρₑ = −p·ρₑ^(p−1)·(E0 − Emin)·(uₑᵀ KE uₑ), uₑ ∈ R²⁴.
Kiểm bằng finite difference trong tests/test_optimize3d.py.
"""

from __future__ import annotations

import numpy as np

from geophys.fea3d import FEA3D


def dc_drho(fea: FEA3D, u: np.ndarray, rho: np.ndarray,
            p: float) -> np.ndarray:
    """Đạo hàm compliance theo mật độ voxel, shape (nelx,nely,nelz), ≤ 0."""
    rho = np.asarray(rho, dtype=np.float64)
    if rho.shape != fea.grid.shape:
        raise ValueError(f"rho shape {rho.shape} — kỳ vọng {fea.grid.shape}")
    if u.shape != (fea.grid.n_dof,):
        raise ValueError(f"u shape {u.shape} — kỳ vọng ({fea.grid.n_dof},)")
    u_e = u[fea.grid.edof_mat]  # (nel, 24)
    quad = np.einsum("ij,jk,ik->i", u_e, fea.ke, u_e)
    dc = -p * rho.ravel() ** (p - 1) * (fea.e0 - fea.e_min) * quad
    return dc.reshape(fea.grid.shape)


def dv_drho(fea: FEA3D) -> np.ndarray:
    """Đạo hàm thể tích — hằng 1 trên lưới voxel đều."""
    return np.ones(fea.grid.shape, dtype=np.float64)
