"""Grid Module 2D — lưới phần tử vuông Q4, ánh xạ element ↔ node, trường mật độ.

Quy ước top88 (xem spec_loader): node cột-trước, y hướng xuống,
element (ex, ey) có 4 node theo thứ tự [n1, n2, n2+1, n1+1]
(trên-trái, trên-phải, dưới-phải, dưới-trái) với
n1 = (nely+1)*ex + ey, n2 = n1 + (nely+1).

CẤM vòng for Python trên từng element — mọi ánh xạ build bằng numpy.
"""

from __future__ import annotations

import numpy as np

from geophys.spec_loader import Spec


class Grid2D:
    """Lưới 2D + trường mật độ khởi tạo từ Spec."""

    def __init__(self, spec: Spec) -> None:
        self.nelx = spec.nelx
        self.nely = spec.nely
        self.nel = spec.nelx * spec.nely
        self.n_nodes = (spec.nelx + 1) * (spec.nely + 1)
        self.n_dof = 2 * self.n_nodes

        self.element_nodes = self._build_element_nodes()  # (nel, 4)
        self.edof_mat = self._build_edof(self.element_nodes)  # (nel, 8)

        self.preserve_mask = self.element_mask(spec.preserve)  # (nelx, nely)
        self.void_mask = self.element_mask(spec.void)

        rho = np.full((self.nelx, self.nely), spec.volfrac, dtype=np.float64)
        rho[self.preserve_mask] = 1.0
        rho[self.void_mask] = 0.0
        self.rho = rho

    # ── ánh xạ node ─────────────────────────────────────────────

    def node_id(self, x, y):
        """(x, y) node → node id. Nhận scalar hoặc numpy array."""
        return np.asarray(x) * (self.nely + 1) + np.asarray(y)

    def node_xy(self, nid):
        """node id → (x, y). Nhận scalar hoặc numpy array."""
        nid = np.asarray(nid)
        return nid // (self.nely + 1), nid % (self.nely + 1)

    # ── ánh xạ element ──────────────────────────────────────────

    def element_id(self, ex, ey):
        return np.asarray(ex) * self.nely + np.asarray(ey)

    def element_xy(self, eid):
        eid = np.asarray(eid)
        return eid // self.nely, eid % self.nely

    def _build_element_nodes(self) -> np.ndarray:
        ex_grid, ey_grid = np.meshgrid(
            np.arange(self.nelx), np.arange(self.nely), indexing="ij")
        n1 = ((self.nely + 1) * ex_grid + ey_grid).ravel()
        n2 = n1 + (self.nely + 1)
        return np.stack([n1, n2, n2 + 1, n1 + 1], axis=1).astype(np.int64)

    @staticmethod
    def _build_edof(element_nodes: np.ndarray) -> np.ndarray:
        nel = element_nodes.shape[0]
        edof = np.empty((nel, 8), dtype=np.int64)
        edof[:, 0::2] = 2 * element_nodes
        edof[:, 1::2] = 2 * element_nodes + 1
        return edof

    # ── vùng ────────────────────────────────────────────────────

    def element_mask(self, regions) -> np.ndarray:
        """Regions (tọa độ element, biên bao gồm) → mask bool (nelx, nely).

        Vòng for trên REGION (số ít, do người khai) — không phải trên element.
        """
        mask = np.zeros((self.nelx, self.nely), dtype=bool)
        for r in regions:
            mask[r.x0:r.x1 + 1, r.y0:r.y1 + 1] = True
        return mask
