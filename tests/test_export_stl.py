"""Acceptance Tầng 1.5 — export STL (spec stage1-t5 mục 8).

Đo thật 08/07/2026 (sau khi sửa bug dấu ν Taubin): box 4.36% · sphere 0.88%
· cantilever optimize 6.23% (biên xám SIMP) · deterministic ✓.
"""

import json

import numpy as np
import pytest
import trimesh

from geophys.export_stl import ExportError, export_stl, rho_to_mesh
from geophys.grid3d import Grid3D
from geophys.optimize3d import optimize3d
from geophys.spec3d import load_spec3d


def test_hop_dac(tmp_path):
    rho = np.zeros((12, 8, 8))
    rho[2:10, 2:6, 2:6] = 1.0
    path, rep = export_stl(rho, tmp_path / "box.stl")
    assert rep["watertight"] and rep["n_components"] == 1
    assert abs(rep["volume_stl"] - 128.0) / 128.0 < 0.05  # đo: 4.36%
    mesh = trimesh.load(path)
    assert mesh.is_watertight
    lo, hi = mesh.bounds
    assert np.all(lo > np.array([1.0, 1.0, 1.0]) - 0.6)
    assert np.all(hi < np.array([10.0, 6.0, 6.0]) + 0.6)


def test_khoi_cau(tmp_path):
    d = {"nelx": 24, "nely": 24, "nelz": 24, "volfrac": 0.4,
         "loads": [{"x": 24, "y": 12, "z": 12, "fy": -1.0}],
         "supports": [{"face": "x0", "dof": "all"}],
         "material": {"E": 1.0, "nu": 0.3}, "simp": {"p": 3.0, "rmin": 1.4},
         "preserve": [{"type": "sphere", "cx": 12.0, "cy": 12.0,
                       "cz": 12.0, "r": 8.0}], "void": []}
    f = tmp_path / "s.json"
    f.write_text(json.dumps(d), encoding="utf-8")
    grid = Grid3D(load_spec3d(f))
    _, rep = export_stl(grid.preserve_mask.astype(float),
                        tmp_path / "sphere.stl")
    theory = 4 / 3 * np.pi * 8 ** 3
    assert rep["watertight"]
    assert abs(rep["volume_stl"] - theory) / theory < 0.03  # đo: 0.88%


def test_ket_qua_optimize_that(tmp_path):
    d = {"nelx": 12, "nely": 6, "nelz": 4, "volfrac": 0.4,
         "loads": [{"x": 12, "y": 6, "z": 2, "fy": -1.0}],
         "supports": [{"face": "x0", "dof": "all"}],
         "material": {"E": 1.0, "nu": 0.3}, "simp": {"p": 3.0, "rmin": 1.3},
         "preserve": [], "void": []}
    f = tmp_path / "s.json"
    f.write_text(json.dumps(d), encoding="utf-8")
    res = optimize3d(load_spec3d(f))
    assert res.converged
    _, rep = export_stl(res.rho, tmp_path / "opt.stl")
    assert rep["watertight"] and rep["n_components"] == 1
    # bài 12×6×4 có tỷ lệ bề mặt/thể tích ~2.5× bài chuẩn → bias biên xám lớn
    # hơn (đo 10.73%); bài chuẩn 60×20×4 đo 6.23% — ngưỡng 10% canh ở deliverable
    assert rep["volume_lech_pct"] < 15.0


def test_nhanh_loi(tmp_path):
    with pytest.raises(ValueError):
        export_stl(np.zeros((4, 4, 4)), tmp_path / "x.stl")  # rỗng vật chất
    with pytest.raises(ValueError):
        export_stl(np.ones((4, 4, 4)), tmp_path / "x.stl", iso=1.2)
    with pytest.raises(ValueError):
        rho_to_mesh(np.ones((4, 4)))  # 2D


def test_deterministic(tmp_path):
    rho = np.zeros((10, 6, 6))
    rho[1:9, 1:5, 1:5] = 1.0
    pa, _ = export_stl(rho, tmp_path / "a.stl")
    pb, _ = export_stl(rho, tmp_path / "b.stl")
    assert pa.read_bytes() == pb.read_bytes()


def test_deliverable_cantilever_ton_tai():
    """STL benchmark 1.3 đã sinh và hợp lệ — nguyên liệu DoD-1.7."""
    from pathlib import Path
    stl = Path(__file__).resolve().parents[1] / "media" / "cantilever3d_60x20x4.stl"
    assert stl.is_file() and stl.stat().st_size > 10_000
    mesh = trimesh.load(stl)
    assert mesh.is_watertight
