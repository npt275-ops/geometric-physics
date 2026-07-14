"""FEA Solver 3D — phần tử H8, sparse KU = F, solver kép direct/CG.

KE tích phân Gauss 2×2×2 trên voxel đơn vị (chính xác cho H8 — kiểm bằng
quadrature bậc cao trong test). Node order khớp Grid3D (LOCK).
Solver: spsolve (bài nhỏ, ground truth) / CG + Jacobi (bài lớn, warm start).

LUẬT SỐNG CÒN (sổ tay sự cố #1 Stage 0): mọi nghiệm phải qua residual check
‖Ku−f‖/‖f‖ ≤ 1e-6 — "giải ra rác không báo lỗi" là lỗi nguy hiểm nhất.
"""

from __future__ import annotations

import numpy as np
from scipy.sparse import coo_matrix, diags
from scipy.sparse.linalg import cg as scipy_cg
from scipy.sparse.linalg import spsolve

from geophys.grid3d import Grid3D
from geophys.spec3d import Spec3D

_RESIDUAL_TOL = 1e-6
_DIRECT_MAX_DOF = 30_000

# 8 node của voxel đơn vị — ĐÚNG thứ tự Grid3D.element_nodes
_NODES_UNIT = np.array([
    [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
    [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
], dtype=np.float64)
# tọa độ quy chiếu tương ứng trong [-1,1]³
_XI_NODES = 2.0 * _NODES_UNIT - 1.0


class SolverError(Exception):
    """KU=F không giải được sạch (suy biến / CG không hội tụ / residual lớn)."""


def _d_matrix(e_mod: float, nu: float) -> np.ndarray:
    lam = e_mod * nu / ((1 + nu) * (1 - 2 * nu))
    mu = e_mod / (2 * (1 + nu))
    d = np.zeros((6, 6))
    d[:3, :3] = lam
    d[np.arange(3), np.arange(3)] = lam + 2 * mu
    d[np.arange(3, 6), np.arange(3, 6)] = mu
    return d


def _ke_quadrature(e_mod: float, nu: float, n_gauss: int) -> np.ndarray:
    """KE H8 với quadrature n_gauss điểm/chiều — dùng chung cho module (2) và test (3)."""
    pts, wts = np.polynomial.legendre.leggauss(n_gauss)
    d_mat = _d_matrix(e_mod, nu)
    ke = np.zeros((24, 24))
    for xi, wx in zip(pts, wts):
        for eta, wy in zip(pts, wts):
            for zeta, wz in zip(pts, wts):
                # dN/dξ (3×8) cho shape function trilinear
                rel = np.array([xi, eta, zeta])
                dn = np.empty((3, 8))
                for a in range(8):
                    s = _XI_NODES[a]
                    dn[0, a] = s[0] * (1 + s[1] * rel[1]) * (1 + s[2] * rel[2]) / 8
                    dn[1, a] = s[1] * (1 + s[0] * rel[0]) * (1 + s[2] * rel[2]) / 8
                    dn[2, a] = s[2] * (1 + s[0] * rel[0]) * (1 + s[1] * rel[1]) / 8
                jac = dn @ _NODES_UNIT  # = I/2 với voxel đơn vị
                dnx = np.linalg.inv(jac) @ dn
                b_mat = np.zeros((6, 24))
                b_mat[0, 0::3] = dnx[0]
                b_mat[1, 1::3] = dnx[1]
                b_mat[2, 2::3] = dnx[2]
                b_mat[3, 0::3] = dnx[1]
                b_mat[3, 1::3] = dnx[0]
                b_mat[4, 1::3] = dnx[2]
                b_mat[4, 2::3] = dnx[1]
                b_mat[5, 0::3] = dnx[2]
                b_mat[5, 2::3] = dnx[0]
                ke += (wx * wy * wz * np.linalg.det(jac)
                       * b_mat.T @ d_mat @ b_mat)
    return ke


def ke_h8(e_mod: float, nu: float) -> np.ndarray:
    """Ma trận độ cứng H8 voxel đơn vị (Gauss 2×2×2 — chính xác cho H8)."""
    return _ke_quadrature(e_mod, nu, 2)


class FEA3D:
    """Solver tuyến tính tĩnh trên Grid3D. Chỉ GỌI Grid3D/Spec3D (STABLE)."""

    def __init__(self, spec: Spec3D, grid: Grid3D) -> None:
        self.spec = spec
        self.grid = grid
        self.e0 = spec.E
        self.e_min = 1e-9 * spec.E
        self.ke = ke_h8(1.0, spec.nu)

        # v2 multi-load: mỗi case một vector lực; case 0 giữ vai trò
        # self.force để đường đơn-case GIỮ NGUYÊN TỪNG BIT (spec stage2-t1)
        cases = getattr(spec, "load_cases", ()) or ((1.0, spec.loads),)
        forces = []
        for _, case_loads in cases:
            force = np.zeros(grid.n_dof, dtype=np.float64)
            for load in case_loads:
                force[3 * load.node] += load.fx
                force[3 * load.node + 1] += load.fy
                force[3 * load.node + 2] += load.fz
            forces.append(force)
        self.forces = forces
        self.weights = tuple(w for w, _ in cases)
        self.force = forces[0]

        fixed = []
        for sup in spec.supports:
            if sup.dof in ("x", "all"):
                fixed.append(3 * sup.node)
            if sup.dof in ("y", "all"):
                fixed.append(3 * sup.node + 1)
            if sup.dof in ("z", "all"):
                fixed.append(3 * sup.node + 2)
        self.fixed = np.unique(np.asarray(fixed, dtype=np.int64))
        self.free = np.setdiff1d(
            np.arange(grid.n_dof, dtype=np.int64), self.fixed)

        edof = grid.edof_mat
        self._i_idx = np.repeat(edof, 24, axis=1).ravel()
        self._j_idx = np.tile(edof, (1, 24)).ravel()
        self.last_cg_iters = 0  # ghi log hiệu năng (tầng 1.4 đọc)

    # ── vật liệu ────────────────────────────────────────────────

    def _check_rho(self, rho: np.ndarray) -> np.ndarray:
        rho = np.asarray(rho, dtype=np.float64)
        if rho.shape != self.grid.shape:
            raise ValueError(
                f"rho shape {rho.shape} — kỳ vọng {self.grid.shape}")
        return rho

    def young(self, rho: np.ndarray, p: float) -> np.ndarray:
        rho = self._check_rho(rho)
        return self.e_min + rho.ravel() ** p * (self.e0 - self.e_min)

    # ── lắp ráp + giải ──────────────────────────────────────────

    def assemble(self, rho: np.ndarray, p: float):
        e_elem = self.young(rho, p)
        s_k = (e_elem[:, None] * self.ke.ravel()[None, :]).ravel()
        n = self.grid.n_dof
        return coo_matrix(
            (s_k, (self._i_idx, self._j_idx)), shape=(n, n)).tocsr()

    def solve(self, rho: np.ndarray, p: float, method: str = "auto",
              x0: np.ndarray | None = None,
              force: np.ndarray | None = None) -> np.ndarray:
        if method not in ("auto", "direct", "cg"):
            raise ValueError(f"method {method!r} — chọn auto|direct|cg")
        if method == "auto":
            method = "direct" if self.grid.n_dof <= _DIRECT_MAX_DOF else "cg"
        if force is None:
            force = self.force
        else:
            force = np.asarray(force, dtype=np.float64)
            if force.shape != (self.grid.n_dof,):
                raise ValueError(
                    f"force shape {force.shape} — kỳ vọng ({self.grid.n_dof},)")

        k_mat = self.assemble(rho, p)
        k_ff = k_mat[self.free, :][:, self.free]
        f_free = force[self.free]
        u = np.zeros(self.grid.n_dof, dtype=np.float64)

        if method == "direct":
            u_free = spsolve(k_ff.tocsc(), f_free)
        else:
            if x0 is not None:
                x0 = np.asarray(x0, dtype=np.float64)
                if x0.shape != (self.grid.n_dof,):
                    raise ValueError(
                        f"x0 shape {x0.shape} — kỳ vọng ({self.grid.n_dof},)")
                x0 = x0[self.free]
            diag = k_ff.diagonal()
            precond = diags(1.0 / np.where(diag > 0, diag, 1.0))
            maxiter = max(100 * int(np.sqrt(self.free.size)), 1000)
            iters = 0

            def _count(_):
                nonlocal iters
                iters += 1

            u_free, info = scipy_cg(k_ff, f_free, x0=x0, M=precond,
                                    rtol=1e-10, atol=0.0, maxiter=maxiter,
                                    callback=_count)
            self.last_cg_iters = iters
            if info > 0:
                res = np.linalg.norm(k_ff @ u_free - f_free) \
                    / max(np.linalg.norm(f_free), 1e-300)
                raise SolverError(
                    f"CG không hội tụ sau {info} vòng (trần {maxiter}), "
                    f"residual {res:.2e} — kiểm tra điều kiện biên/Emin")

        finite = bool(np.all(np.isfinite(u_free)))
        rel_res = np.inf
        if finite:
            rel_res = np.linalg.norm(k_ff @ u_free - f_free) \
                / max(np.linalg.norm(f_free), 1e-300)
        if not finite or rel_res > _RESIDUAL_TOL:
            raise SolverError(
                f"[{method}] K suy biến hoặc nghiệm rác: residual "
                f"{'∞' if not finite else f'{rel_res:.2e}'} > {_RESIDUAL_TOL} "
                "— nghi thiếu ràng buộc rigid body (3 tịnh tiến + 3 xoay)")
        u[self.free] = u_free
        return u

    # ── hậu xử lý ───────────────────────────────────────────────

    def compliance(self, u: np.ndarray,
                   force: np.ndarray | None = None) -> float:
        """c = F·U (mặc định case 0 — hành vi v1 giữ nguyên)."""
        f = self.force if force is None else force
        return float(f @ u)

    def element_energy(self, u: np.ndarray, rho: np.ndarray,
                       p: float) -> np.ndarray:
        """Năng lượng biến dạng từng voxel (nelx,nely,nelz). Σ = ½·F·U."""
        e_elem = self.young(rho, p)
        u_e = u[self.grid.edof_mat]  # (nel, 24)
        quad = np.einsum("ij,jk,ik->i", u_e, self.ke, u_e)
        return (0.5 * e_elem * quad).reshape(self.grid.shape)
