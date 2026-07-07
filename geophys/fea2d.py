"""FEA Solver 2D — phần tử Q4, sparse KU = F, compliance + năng lượng element.

Element vuông 1×1, plane stress, KE giải tích theo top88.
Thứ tự dof khớp Grid2D.element_nodes: [UL, UR, LR, LL] (y hướng xuống).
Nội suy SIMP: E(ρ) = Emin + ρ^p (E0 − Emin), Emin = 1e-9·E0.

CẤM vòng for Python trên element — assembly và energy thuần numpy.
"""

from __future__ import annotations

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

from geophys.grid2d import Grid2D
from geophys.spec_loader import Spec


class SolverError(Exception):
    """Hệ KU=F không giải được sạch (suy biến / NaN / residual lớn).

    Ghi chú kiến trúc: sẽ merge vào geophys.errors ở lần mở khóa
    protected kế tiếp — không tự sửa file protected.
    """


def ke_q4(e_mod: float, nu: float) -> np.ndarray:
    """Ma trận độ cứng element Q4 1×1, plane stress (giải tích top88)."""
    k = np.array([
        1 / 2 - nu / 6, 1 / 8 + nu / 8, -1 / 4 - nu / 12, -1 / 8 + 3 * nu / 8,
        -1 / 4 + nu / 12, -1 / 8 - nu / 8, nu / 6, 1 / 8 - 3 * nu / 8,
    ])
    idx = np.array([
        [0, 1, 2, 3, 4, 5, 6, 7],
        [1, 0, 7, 6, 5, 4, 3, 2],
        [2, 7, 0, 5, 6, 3, 4, 1],
        [3, 6, 5, 0, 7, 2, 1, 4],
        [4, 5, 6, 7, 0, 1, 2, 3],
        [5, 4, 3, 2, 1, 0, 7, 6],
        [6, 3, 4, 1, 2, 7, 0, 5],
        [7, 2, 1, 4, 3, 6, 5, 0],
    ])
    return e_mod / (1 - nu ** 2) * k[idx]


class FEA2D:
    """Solver tuyến tính tĩnh trên Grid2D. Chỉ GỌI Grid2D/Spec (STABLE)."""

    def __init__(self, spec: Spec, grid: Grid2D) -> None:
        self.spec = spec
        self.grid = grid
        self.e0 = spec.E
        self.e_min = 1e-9 * spec.E
        self.ke = ke_q4(1.0, spec.nu)  # E đơn vị — scale bằng E(ρ) khi lắp ráp

        # Vector lực toàn cục
        force = np.zeros(grid.n_dof, dtype=np.float64)
        for load in spec.loads:
            force[2 * load.node] += load.fx
            force[2 * load.node + 1] += load.fy
        self.force = force

        # Điều kiện biên
        fixed = []
        for sup in spec.supports:
            if sup.dof in ("x", "both"):
                fixed.append(2 * sup.node)
            if sup.dof in ("y", "both"):
                fixed.append(2 * sup.node + 1)
        self.fixed = np.unique(np.asarray(fixed, dtype=np.int64))
        self.free = np.setdiff1d(
            np.arange(grid.n_dof, dtype=np.int64), self.fixed)

        # Chỉ số COO precompute một lần, tái dùng mỗi lần assemble
        edof = grid.edof_mat
        self._i_idx = np.repeat(edof, 8, axis=1).ravel()
        self._j_idx = np.tile(edof, (1, 8)).ravel()

    # ── nội suy vật liệu ────────────────────────────────────────

    def _check_rho(self, rho: np.ndarray) -> np.ndarray:
        rho = np.asarray(rho, dtype=np.float64)
        expected = (self.grid.nelx, self.grid.nely)
        if rho.shape != expected:
            raise ValueError(
                f"rho shape {rho.shape} — kỳ vọng {expected} (nelx, nely)")
        return rho

    def young(self, rho: np.ndarray, p: float) -> np.ndarray:
        """E(ρ) từng element, trả về mảng phẳng theo thứ tự element id."""
        rho = self._check_rho(rho)
        return self.e_min + rho.ravel() ** p * (self.e0 - self.e_min)

    # ── lắp ráp + giải ──────────────────────────────────────────

    def assemble(self, rho: np.ndarray, p: float):
        e_elem = self.young(rho, p)
        s_k = (e_elem[:, None] * self.ke.ravel()[None, :]).ravel()
        n = self.grid.n_dof
        return coo_matrix(
            (s_k, (self._i_idx, self._j_idx)), shape=(n, n)).tocsr()

    def solve(self, rho: np.ndarray, p: float) -> np.ndarray:
        k_mat = self.assemble(rho, p)
        k_ff = k_mat[self.free, :][:, self.free]
        u = np.zeros(self.grid.n_dof, dtype=np.float64)
        f_free = self.force[self.free]
        u_free = spsolve(k_ff.tocsc(), f_free)
        # Hai lớp kiểm: (1) NaN/Inf khi scipy phát hiện suy biến chính xác;
        # (2) residual — suy biến do làm tròn cho nghiệm hữu hạn nhưng SAI,
        #     nghiệm thật phải thỏa ||K·u − f|| nhỏ so với ||f||.
        finite = bool(np.all(np.isfinite(u_free)))
        rel_res = np.inf
        if finite:
            residual = np.linalg.norm(k_ff @ u_free - f_free)
            rel_res = residual / max(np.linalg.norm(f_free), 1e-300)
        if not finite or rel_res > 1e-6:
            raise SolverError(
                "K suy biến (nghiệm NaN/Inf hoặc residual "
                f"{'∞' if not finite else f'{rel_res:.2e}'} > 1e-6). "
                "Nghi vấn: thiếu ràng buộc rigid body "
                "(cần khóa đủ 2 tịnh tiến + 1 xoay trong 2D).")
        u[self.free] = u_free
        return u

    # ── hậu xử lý ───────────────────────────────────────────────

    def compliance(self, u: np.ndarray) -> float:
        """c = F·U."""
        return float(self.force @ u)

    def element_energy(self, u: np.ndarray, rho: np.ndarray,
                       p: float) -> np.ndarray:
        """Năng lượng biến dạng từng element, shape (nelx, nely).

        Tổng toàn miền = ½·F·U (định lý Clapeyron) — có test riêng.
        """
        e_elem = self.young(rho, p)
        u_e = u[self.grid.edof_mat]  # (nel, 8)
        quad = np.einsum("ij,jk,ik->i", u_e, self.ke, u_e)
        energy = 0.5 * e_elem * quad
        return energy.reshape(self.grid.nelx, self.grid.nely)
