"""Acceptance Tầng 0.3 — OC Update (spec stage0-t3 mục 8).

Đo thật 07/07: volume err 3.6e-08 · move/preserve/void ✓ · infeasible bắt được.
"""

import numpy as np
import pytest

from geophys.oc_update import oc_update

SHAPE = (8, 6)


@pytest.fixture()
def inputs():
    rng = np.random.default_rng(42)
    rho = rng.uniform(0.3, 0.9, SHAPE)
    dc = -rng.uniform(0.1, 10.0, SHAPE)
    dv = np.ones(SHAPE)
    no_mask = np.zeros(SHAPE, dtype=bool)
    return rho, dc, dv, no_mask


def test_volume_dung_target(inputs):
    rho, dc, dv, no_mask = inputs
    xnew = oc_update(rho, dc, dv, 0.5, no_mask, no_mask)
    assert abs(xnew.mean() - 0.5) < 1e-3  # đo thật: 3.6e-08


def test_move_limit_va_bien(inputs):
    rho, dc, dv, no_mask = inputs
    xnew = oc_update(rho, dc, dv, 0.5, no_mask, no_mask, move=0.2)
    assert (np.abs(xnew - rho) <= 0.2 + 1e-12).all()
    assert (xnew >= 0.0).all() and (xnew <= 1.0).all()


def test_preserve_void_tuyet_doi(inputs):
    rho, dc, dv, _ = inputs
    pm = np.zeros(SHAPE, dtype=bool)
    vm = np.zeros(SHAPE, dtype=bool)
    pm[0, :] = True
    vm[7, 0] = True
    xnew = oc_update(rho, dc, dv, 0.5, pm, vm)
    assert (xnew[pm] == 1.0).all()
    assert (xnew[vm] == 0.0).all()
    assert abs(xnew.mean() - 0.5) < 1e-3


def test_don_dieu_theo_gradient():
    """ρ đều → xnew phải xếp hạng đúng theo −dc (vùng chưa chạm move/biên)."""
    rho = np.full(SHAPE, 0.5)
    rng = np.random.default_rng(1)
    dc = -rng.uniform(0.5, 5.0, SHAPE)
    dv = np.ones(SHAPE)
    no_mask = np.zeros(SHAPE, dtype=bool)
    xnew = oc_update(rho, dc, dv, 0.5, no_mask, no_mask, move=0.2)
    inner = (xnew > 0.3 + 1e-9) & (xnew < 0.7 - 1e-9)  # chưa chạm move limit
    if inner.sum() >= 2:
        order_dc = np.argsort(-dc[inner])   # tăng dần theo −dc...
        vals = xnew[inner][order_dc]
        assert (np.diff(vals) >= -1e-12).all()


def test_bat_kha_thi_raise(inputs):
    rho, dc, dv, no_mask = inputs
    pm = np.zeros(SHAPE, dtype=bool)
    pm[:4, :] = True  # preserve 24/48 element
    with pytest.raises(ValueError):
        oc_update(rho, dc, dv, 0.3, pm, no_mask)  # target 14.4 < 24
    vm = np.zeros(SHAPE, dtype=bool)
    vm[:4, :] = True
    with pytest.raises(ValueError):
        oc_update(rho, dc, dv, 0.9, no_mask, vm)  # target 43.2 > 24 khả dụng


def test_sai_shape_raise(inputs):
    rho, dc, dv, no_mask = inputs
    with pytest.raises(ValueError):
        oc_update(rho, dc.T, dv, 0.5, no_mask, no_mask)


def test_dc_duong_nhieu_khong_pha(inputs):
    """dc dương (nhiễu số) bị kẹp 0 — không NaN, không thưởng vật liệu."""
    rho, dc, dv, no_mask = inputs
    dc_noisy = dc.copy()
    dc_noisy[2, 2] = +0.5
    xnew = oc_update(rho, dc_noisy, dv, 0.5, no_mask, no_mask)
    assert np.isfinite(xnew).all()
    # element gradient dương chỉ có thể mất vật liệu (be = 0 → x giảm hết move)
    assert xnew[2, 2] <= rho[2, 2] - 0.2 + 1e-12 or xnew[2, 2] == 0.0


def test_deterministic(inputs):
    rho, dc, dv, no_mask = inputs
    a = oc_update(rho, dc, dv, 0.5, no_mask, no_mask)
    b = oc_update(rho, dc, dv, 0.5, no_mask, no_mask)
    assert np.array_equal(a, b)
