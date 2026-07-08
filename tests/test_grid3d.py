"""Acceptance Tầng 1.1 — Grid3D (spec stage1-t1 mục 8).

Đo thật 08/07/2026: sphere 1.461% · cylinder 1.339% (ngưỡng < 2%) · box exact.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from geophys.errors import SpecError
from geophys.grid3d import Grid3D
from geophys.spec3d import load_spec3d

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"

BASE = {"nelx": 24, "nely": 24, "nelz": 24, "volfrac": 0.4,
        "loads": [{"x": 24, "y": 12, "z": 12, "fy": -1.0}],
        "supports": [{"face": "x0", "dof": "all"}],
        "material": {"E": 1.0, "nu": 0.3}, "simp": {"p": 3.0, "rmin": 1.4},
        "preserve": [], "void": []}


def mk(tmp_path, **override):
    d = {**BASE, **override}
    f = tmp_path / "s.json"
    f.write_text(json.dumps(d), encoding="utf-8")
    return Grid3D(load_spec3d(f))


@pytest.fixture(scope="module")
def cant():
    return Grid3D(load_spec3d(EXAMPLES / "spec3d_cantilever_60x20x4.json"))


# ── công thức đếm ───────────────────────────────────────────────

def test_dem_node_element_dof(cant):
    assert cant.n_nodes == 61 * 21 * 5
    assert cant.nel == 60 * 20 * 4
    assert cant.n_dof == 3 * cant.n_nodes
    assert cant.element_nodes.shape == (cant.nel, 8)
    assert cant.edof_mat.shape == (cant.nel, 24)


# ── round-trip toàn lưới ────────────────────────────────────────

def test_round_trip_node(cant):
    nids = np.arange(cant.n_nodes)
    x, y, z = cant.node_xyz(nids)
    assert np.array_equal(cant.node_id(x, y, z), nids)


def test_round_trip_element(cant):
    eids = np.arange(cant.nel)
    ex, ey, ez = cant.element_xyz(eids)
    assert np.array_equal(cant.element_id(ex, ey, ez), eids)


def test_h8_dung_hinh_hoc(cant):
    eids = np.arange(cant.nel)
    ex, ey, ez = cant.element_xyz(eids)
    expected = np.stack([
        cant.node_id(ex, ey, ez), cant.node_id(ex + 1, ey, ez),
        cant.node_id(ex + 1, ey + 1, ez), cant.node_id(ex, ey + 1, ez),
        cant.node_id(ex, ey, ez + 1), cant.node_id(ex + 1, ey, ez + 1),
        cant.node_id(ex + 1, ey + 1, ez + 1), cant.node_id(ex, ey + 1, ez + 1),
    ], axis=1)
    assert np.array_equal(cant.element_nodes, expected)


def test_edof_khop_element_nodes(cant):
    for k in range(3):
        assert np.array_equal(cant.edof_mat[:, k::3],
                              3 * cant.element_nodes + k)


# ── rasterize hình khối ─────────────────────────────────────────

def test_box_chinh_xac_tung_voxel(tmp_path):
    g = mk(tmp_path, preserve=[{"type": "box", "x0": 2, "y0": 3, "z0": 4,
                                "x1": 5, "y1": 7, "z1": 9}])
    assert int(g.preserve_mask.sum()) == 4 * 5 * 6
    assert g.preserve_mask[2:6, 3:8, 4:10].all()


def test_sphere_the_tich(tmp_path):
    g = mk(tmp_path, void=[{"type": "sphere", "cx": 12.0, "cy": 12.0,
                            "cz": 12.0, "r": 8.0}])
    theory = 4 / 3 * np.pi * 8 ** 3
    assert abs(int(g.void_mask.sum()) - theory) / theory < 0.02  # đo: 1.461%


@pytest.mark.parametrize("axis,extra", [
    ("z", {"cx": 12.0, "cy": 12.0, "z0": 0, "z1": 23}),
    ("x", {"cy": 12.0, "cz": 12.0, "x0": 0, "x1": 23}),
])
def test_cylinder_the_tich(tmp_path, axis, extra):
    prim = {"type": "cylinder", "axis": axis, "r": 7.0, **extra}
    g = mk(tmp_path, void=[prim])
    theory = np.pi * 7 ** 2 * 24
    assert abs(int(g.void_mask.sum()) - theory) / theory < 0.02  # đo: 1.339%


def test_overlap_preserve_void_bi_chan(tmp_path):
    with pytest.raises(SpecError):
        mk(tmp_path,
           preserve=[{"type": "box", "x0": 10, "y0": 10, "z0": 10,
                      "x1": 14, "y1": 14, "z1": 14}],
           void=[{"type": "sphere", "cx": 12.0, "cy": 12.0, "cz": 12.0,
                  "r": 3.0}])


# ── trường mật độ ───────────────────────────────────────────────

def test_rho_init(tmp_path):
    g = mk(tmp_path, preserve=[{"type": "box", "x0": 0, "y0": 0, "z0": 0,
                                "x1": 1, "y1": 23, "z1": 23}])
    assert g.rho.shape == (24, 24, 24)
    assert (g.rho[g.preserve_mask] == 1.0).all()
    rest = ~(g.preserve_mask | g.void_mask)
    assert (g.rho[rest] == 0.4).all()


def test_deterministic():
    spec = load_spec3d(EXAMPLES / "spec3d_primitives_20.json")
    g1, g2 = Grid3D(spec), Grid3D(spec)
    assert np.array_equal(g1.rho, g2.rho)
    assert np.array_equal(g1.edof_mat, g2.edof_mat)
