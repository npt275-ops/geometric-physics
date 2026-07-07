"""Acceptance Tầng 0.3 — sensitivity (spec stage0-t3 mục 8).

FD check là phép kiểm quan trọng nhất dự án: gradient sai nhưng vòng lặp
vẫn "ra hình gì đó" là loại bug nguy hiểm nhất. Đo thật 07/07: 4.13e-06.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from geophys.fea2d import FEA2D
from geophys.grid2d import Grid2D
from geophys.sensitivity import dc_drho, dv_drho
from geophys.spec_loader import load_spec


def make_spec(tmp_path, data):
    f = tmp_path / "spec.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    return load_spec(f)


@pytest.fixture(scope="module")
def small_cantilever(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("sens")
    spec = make_spec(tmp, {
        "nelx": 8, "nely": 6, "volfrac": 0.5,
        "loads": [{"x": 8, "y": 3, "fx": 0.0, "fy": -1.0}],
        "supports": [{"edge": "left", "dof": "both"}],
        "material": {"E": 1.0, "nu": 0.3},
        "simp": {"p": 3.0, "rmin": 1.5},
        "preserve": [], "void": []})
    grid = Grid2D(spec)
    fea = FEA2D(spec, grid)
    rng = np.random.default_rng(42)
    rho = rng.uniform(0.3, 0.9, (8, 6))
    u = fea.solve(rho, 3.0)
    return fea, rho, u, rng


def test_fd_check_15_element_ngau_nhien(small_cantilever):
    """Central difference h=1e-6 — ngưỡng spec < 1%, đo thật 4.1e-06."""
    fea, rho, u, rng = small_cantilever
    dc = dc_drho(fea, u, rho, 3.0)
    h = 1e-6
    for idx in rng.choice(48, 15, replace=False):
        ex, ey = int(idx) // 6, int(idx) % 6
        rho_p = rho.copy()
        rho_p[ex, ey] += h
        rho_m = rho.copy()
        rho_m[ex, ey] -= h
        fd = (fea.compliance(fea.solve(rho_p, 3.0))
              - fea.compliance(fea.solve(rho_m, 3.0))) / (2 * h)
        assert abs((dc[ex, ey] - fd) / fd) < 0.01


@pytest.mark.parametrize("fill", [0.2, 0.5, 1.0])
def test_dc_khong_duong_toan_mien(small_cantilever, fill):
    fea, _, _, _ = small_cantilever
    rho = np.full((8, 6), fill)
    u = fea.solve(rho, 3.0)
    dc = dc_drho(fea, u, rho, 3.0)
    assert (dc <= 0).all()
    assert dc.shape == (8, 6)


def test_dv_bang_1(small_cantilever):
    fea, *_ = small_cantilever
    assert np.array_equal(dv_drho(fea), np.ones((8, 6)))


def test_sai_shape_raise(small_cantilever):
    fea, rho, u, _ = small_cantilever
    with pytest.raises(ValueError):
        dc_drho(fea, u, rho.T, 3.0)
    with pytest.raises(ValueError):
        dc_drho(fea, u[:-2], rho, 3.0)


def test_deterministic(small_cantilever):
    fea, rho, u, _ = small_cantilever
    a = dc_drho(fea, u, rho, 3.0)
    b = dc_drho(fea, u, rho, 3.0)
    assert np.array_equal(a, b)
