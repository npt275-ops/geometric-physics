"""Acceptance Tầng 0.1 — phần Grid2D (spec mục 8)."""

from pathlib import Path

import numpy as np
import pytest

from geophys.grid2d import Grid2D
from geophys.spec_loader import load_spec

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


@pytest.fixture(scope="module")
def mbb():
    return Grid2D(load_spec(EXAMPLES / "spec_mbb_60x20.json"))


@pytest.fixture(scope="module")
def pv():
    return Grid2D(load_spec(EXAMPLES / "spec_preserve_void_20x20.json"))


# ── công thức đếm ───────────────────────────────────────────────

def test_so_node_va_element(mbb):
    assert mbb.n_nodes == (60 + 1) * (20 + 1)
    assert mbb.nel == 60 * 20
    assert mbb.n_dof == 2 * mbb.n_nodes
    assert mbb.edof_mat.shape == (mbb.nel, 8)
    assert mbb.element_nodes.shape == (mbb.nel, 4)


# ── round-trip toàn lưới, 100% khớp ─────────────────────────────

def test_round_trip_node_toan_luoi(mbb):
    nids = np.arange(mbb.n_nodes)
    x, y = mbb.node_xy(nids)
    assert np.array_equal(mbb.node_id(x, y), nids)


def test_round_trip_element_toan_luoi(mbb):
    eids = np.arange(mbb.nel)
    # element → node góc trên-trái n1 → (ex, ey) → element
    n1 = mbb.element_nodes[:, 0]
    ex, ey = mbb.node_xy(n1)
    assert np.array_equal(mbb.element_id(ex, ey), eids)
    # và ngược: element_xy → element_id
    ex2, ey2 = mbb.element_xy(eids)
    assert np.array_equal(mbb.element_id(ex2, ey2), eids)


def test_bon_node_dung_hinh_hoc(mbb):
    """4 node của mỗi element phải đúng vị trí hình học (toàn lưới)."""
    eids = np.arange(mbb.nel)
    ex, ey = mbb.element_xy(eids)
    expected = np.stack([
        mbb.node_id(ex, ey),          # trên-trái
        mbb.node_id(ex + 1, ey),      # trên-phải
        mbb.node_id(ex + 1, ey + 1),  # dưới-phải
        mbb.node_id(ex, ey + 1),      # dưới-trái
    ], axis=1)
    assert np.array_equal(mbb.element_nodes, expected)


def test_edof_khop_element_nodes(mbb):
    assert np.array_equal(mbb.edof_mat[:, 0::2], 2 * mbb.element_nodes)
    assert np.array_equal(mbb.edof_mat[:, 1::2], 2 * mbb.element_nodes + 1)


# ── trường mật độ sau mask ──────────────────────────────────────

def test_mat_do_preserve_void_volfrac(pv):
    rho = pv.rho
    assert rho.shape == (20, 20)
    # preserve toàn 1.0
    assert np.all(rho[pv.preserve_mask] == 1.0)
    # void toàn 0.0
    assert np.all(rho[pv.void_mask] == 0.0)
    # phần còn lại đúng volfrac
    rest = ~(pv.preserve_mask | pv.void_mask)
    assert np.all(rho[rest] == 0.4)
    # kích thước mask khớp spec: preserve 2 cột × 20 hàng, void 3 × 4
    assert pv.preserve_mask.sum() == 2 * 20
    assert pv.void_mask.sum() == 3 * 4


def test_khong_vung_thi_toan_volfrac(mbb):
    assert np.all(mbb.rho == 0.5)
    assert mbb.preserve_mask.sum() == 0
    assert mbb.void_mask.sum() == 0


# ── deterministic ───────────────────────────────────────────────

def test_deterministic_hai_lan_giong_het():
    spec = load_spec(EXAMPLES / "spec_preserve_void_20x20.json")
    g1, g2 = Grid2D(spec), Grid2D(spec)
    assert np.array_equal(g1.rho, g2.rho)
    assert np.array_equal(g1.edof_mat, g2.edof_mat)
