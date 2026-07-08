"""Grid Module 3D — voxel H8, ánh xạ element ↔ node, rasterize hình khối.

Quy ước (LOCK, xem specs/stage1-t1): node_id = z·(nelx+1)(nely+1) + x·(nely+1) + y;
element_id = ravel C-order (ex,ey,ez); H8: 4 node đáy z rồi 4 node đỉnh z+1;
dof node n = [3n, 3n+1, 3n+2]. rho shape (nelx, nely, nelz).

CẤM vòng for Python trên voxel — rasterize/edof thuần numpy
(vòng for trên PRIMITIVE — số ít do người khai — được phép).
"""

from __future__ import annotations

import numpy as np

from geophys.errors import SpecError
from geophys.spec3d import Primitive, Spec3D


class Grid3D:
    """Lưới voxel 3D + trường mật độ khởi tạo từ Spec3D."""

    def __init__(self, spec: Spec3D) -> None:
        self.nelx, self.nely, self.nelz = spec.nelx, spec.nely, spec.nelz
        self.shape = (self.nelx, self.nely, self.nelz)
        self.nel = self.nelx * self.nely * self.nelz
        self.n_nodes = (self.nelx + 1) * (self.nely + 1) * (self.nelz + 1)
        self.n_dof = 3 * self.n_nodes

        self.element_nodes = self._build_element_nodes()  # (nel, 8)
        self.edof_mat = self._build_edof(self.element_nodes)  # (nel, 24)

        self.preserve_mask = self.rasterize(spec.preserve)
        self.void_mask = self.rasterize(spec.void)
        overlap = self.preserve_mask & self.void_mask
        if overlap.any():
            n_over = int(overlap.sum())
            raise SpecError("preserve/void",
                            f"vùng bảo tồn giao vùng cấm tại {n_over} voxel",
                            "hai loại vùng phải rời nhau sau rasterize")

        rho = np.full(self.shape, spec.volfrac, dtype=np.float64)
        rho[self.preserve_mask] = 1.0
        rho[self.void_mask] = 0.0
        self.rho = rho

    # ── ánh xạ node ─────────────────────────────────────────────

    def node_id(self, x, y, z):
        x, y, z = np.asarray(x), np.asarray(y), np.asarray(z)
        return (z * (self.nelx + 1) * (self.nely + 1)
                + x * (self.nely + 1) + y)

    def node_xyz(self, nid):
        nid = np.asarray(nid)
        per_layer = (self.nelx + 1) * (self.nely + 1)
        z, rem = nid // per_layer, nid % per_layer
        return rem // (self.nely + 1), rem % (self.nely + 1), z

    # ── ánh xạ element ──────────────────────────────────────────

    def element_id(self, ex, ey, ez):
        return np.ravel_multi_index(
            (np.asarray(ex), np.asarray(ey), np.asarray(ez)), self.shape)

    def element_xyz(self, eid):
        return np.unravel_index(np.asarray(eid), self.shape)

    def _build_element_nodes(self) -> np.ndarray:
        ex, ey, ez = np.meshgrid(np.arange(self.nelx), np.arange(self.nely),
                                 np.arange(self.nelz), indexing="ij")
        ex, ey, ez = ex.ravel(), ey.ravel(), ez.ravel()  # C-order khớp element_id
        base = [self.node_id(ex, ey, ez), self.node_id(ex + 1, ey, ez),
                self.node_id(ex + 1, ey + 1, ez), self.node_id(ex, ey + 1, ez)]
        top = [self.node_id(ex, ey, ez + 1), self.node_id(ex + 1, ey, ez + 1),
               self.node_id(ex + 1, ey + 1, ez + 1),
               self.node_id(ex, ey + 1, ez + 1)]
        return np.stack(base + top, axis=1).astype(np.int64)

    @staticmethod
    def _build_edof(element_nodes: np.ndarray) -> np.ndarray:
        nel = element_nodes.shape[0]
        edof = np.empty((nel, 24), dtype=np.int64)
        edof[:, 0::3] = 3 * element_nodes
        edof[:, 1::3] = 3 * element_nodes + 1
        edof[:, 2::3] = 3 * element_nodes + 2
        return edof

    # ── rasterize hình khối tại tâm voxel ───────────────────────

    def rasterize(self, primitives) -> np.ndarray:
        """Primitives → mask bool (nelx, nely, nelz). Vòng for trên PRIMITIVE."""
        mask = np.zeros(self.shape, dtype=bool)
        if not primitives:
            return mask
        cx, cy, cz = np.meshgrid(
            np.arange(self.nelx) + 0.5, np.arange(self.nely) + 0.5,
            np.arange(self.nelz) + 0.5, indexing="ij")
        centers = {"x": cx, "y": cy, "z": cz}
        for prim in primitives:
            if prim.kind == "box":
                x0, y0, z0, x1, y1, z1 = prim.params
                mask[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = True
            elif prim.kind == "sphere":
                scx, scy, scz, r = prim.params
                mask |= ((cx - scx) ** 2 + (cy - scy) ** 2
                         + (cz - scz) ** 2) <= r ** 2
            else:  # cylinder
                axis, c1, c2, r, a0, a1 = prim.params
                perp = [a for a in ("x", "y", "z") if a != axis]
                radial = ((centers[perp[0]] - c1) ** 2
                          + (centers[perp[1]] - c2) ** 2) <= r ** 2
                along = (centers[axis] >= a0) & (centers[axis] <= a1 + 1.0)
                mask |= radial & along
        return mask
