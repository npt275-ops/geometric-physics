"""Acceptance Tầng 0.3 — SensitivityFilter (spec stage0-t3 mục 8).

Đo thật 07/07: vs reference 2.7e-15 · trường hằng 4.4e-16 · checkerboard 0.227.
"""

import numpy as np
import pytest

from geophys.filter2d import SensitivityFilter


def reference_filter(rho, dc, rmin):
    """Bản O(N²) tường minh — đường tính ĐỘC LẬP, chỉ dùng trong test."""
    nx, ny = rho.shape
    out = np.zeros((nx, ny))
    for i in range(nx):
        for j in range(ny):
            num = 0.0
            wsum = 0.0
            for i2 in range(nx):
                for j2 in range(ny):
                    w = max(0.0, rmin - np.hypot(i - i2, j - j2))
                    num += w * rho[i2, j2] * dc[i2, j2]
                    wsum += w
            out[i, j] = num / (wsum * max(rho[i, j], 1e-3))
    return out


def test_khop_reference_o_n2():
    rng = np.random.default_rng(7)
    rho = rng.uniform(0.1, 1.0, (7, 5))
    dc = -rng.uniform(0.1, 5.0, (7, 5))
    fast = SensitivityFilter(7, 5, 2.1).apply(rho, dc)
    assert np.abs(fast - reference_filter(rho, dc, 2.1)).max() < 1e-12


def test_bao_toan_truong_hang():
    filt = SensitivityFilter(7, 5, 2.1)
    out = filt.apply(np.full((7, 5), 0.6), np.full((7, 5), -2.0))
    assert np.abs(out + 2.0).max() < 1e-12


def test_dap_checkerboard():
    """DoD-0.2: pattern bàn cờ phải bị bộ lọc triệt mạnh (đo thật: 22.7%)."""
    filt = SensitivityFilter(12, 10, 1.5)
    cb = (np.indices((12, 10)).sum(0) % 2) * 2.0 - 1.0
    out = filt.apply(np.full((12, 10), 0.5), cb)
    assert np.abs(out).max() < 0.5 * np.abs(cb).max()


def test_rmin_khong_hop_le():
    with pytest.raises(ValueError):
        SensitivityFilter(5, 5, 0.0)
    with pytest.raises(ValueError):
        SensitivityFilter(5, 5, -1.5)


def test_sai_shape_raise():
    filt = SensitivityFilter(7, 5, 1.5)
    with pytest.raises(ValueError):
        filt.apply(np.ones((5, 7)), np.ones((7, 5)))
    with pytest.raises(ValueError):
        filt.apply(np.ones((7, 5)), np.ones((5, 7)))


def test_deterministic():
    rng = np.random.default_rng(3)
    rho = rng.uniform(0.1, 1.0, (9, 6))
    dc = -rng.uniform(0.1, 3.0, (9, 6))
    filt = SensitivityFilter(9, 6, 1.8)
    assert np.array_equal(filt.apply(rho, dc), filt.apply(rho, dc))
