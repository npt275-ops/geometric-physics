"""Acceptance Tầng 1.2 — FEA 3D H8 + CG (spec stage1-t2 mục 8).

Đo thật 08/07/2026: KE 2v3 Gauss 1.67e-16 · patch 1.1e-14 · Timoshenko 2.84%
· CG vs direct 9.1e-13 · warm start 0 vòng.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from geophys.fea3d import FEA3D, SolverError, _ke_quadrature, ke_h8
from geophys.grid3d import Grid3D
from geophys.spec3d import load_spec3d


def mk(tmp_path, d):
    f = tmp_path / "s.json"
    f.write_text(json.dumps(d), encoding="utf-8")
    return load_spec3d(f)


def face_loads(x, ny, nz, name, total):
    """Tải phân bố đều trên mặt x=const, trọng số góc/cạnh chuẩn."""
    loads = []
    for y in range(ny + 1):
        for z in range(nz + 1):
            w = (0.5 if y in (0, ny) else 1.0) * (0.5 if z in (0, nz) else 1.0)
            loads.append({"x": x, "y": y, "z": z, name: total * w / (ny * nz)})
    return loads


# ── KE ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("nu", [0.25, 0.3, 0.4])
def test_ke_hai_bac_quadrature_trung_nhau(nu):
    """Gauss 2 điểm chính xác cho H8 → 2×2×2 phải trùng 3×3×3 đến máy."""
    assert np.abs(ke_h8(1.0, nu) - _ke_quadrature(1.0, nu, 3)).max() < 1e-12


def test_ke_doi_xung_va_6_rigid_modes():
    ke = ke_h8(1.0, 0.3)
    assert np.abs(ke - ke.T).max() < 1e-14
    ev = np.linalg.eigvalsh(ke)
    assert int((np.abs(ev) < 1e-12).sum()) == 6   # 3 tịnh tiến + 3 xoay
    assert int((ev > 1e-12).sum()) == 18


# ── Patch test 3D ───────────────────────────────────────────────

@pytest.fixture(scope="module")
def patch(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("patch3d")
    n = 4
    spec = mk(tmp, {
        "nelx": n, "nely": n, "nelz": n, "volfrac": 0.5,
        "loads": face_loads(n, n, n, "fx", float(n * n)),
        "supports": [{"face": "x0", "dof": "x"},
                     {"x": 0, "y": 0, "z": 0, "dof": "all"},
                     {"x": 0, "y": n, "z": 0, "dof": "z"},
                     {"x": 0, "y": 0, "z": n, "dof": "y"}],
        "material": {"E": 1.0, "nu": 0.3},
        "simp": {"p": 3.0, "rmin": 1.4}, "preserve": [], "void": []})
    grid = Grid3D(spec)
    fea = FEA3D(spec, grid)
    u = fea.solve(np.ones((n, n, n)), 3.0)
    return grid, fea, u


def test_patch_chuyen_vi_chinh_xac(patch):
    grid, _, u = patch
    n = 4  # σ = 1, E = 1 → ux(L) = L
    ids = [grid.node_id(n, y, z) for y in range(n + 1) for z in range(n + 1)]
    assert np.abs(u[3 * np.asarray(ids)] - float(n)).max() < 1e-9


def test_patch_nang_luong_dong_nhat(patch):
    _, fea, u = patch
    en = fea.element_energy(u, np.ones((4, 4, 4)), 3.0)
    assert (en.max() - en.min()) / en.mean() < 1e-9


# ── Cantilever 3D vs Timoshenko ─────────────────────────────────

@pytest.fixture(scope="module")
def cantilever(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("cant3d")
    length, h, b = 32, 8, 8
    spec = mk(tmp, {
        "nelx": length, "nely": h, "nelz": b, "volfrac": 0.5,
        "loads": face_loads(length, h, b, "fy", -1.0),
        "supports": [{"face": "x0", "dof": "all"}],
        "material": {"E": 1.0, "nu": 0.3},
        "simp": {"p": 3.0, "rmin": 1.5}, "preserve": [], "void": []})
    grid = Grid3D(spec)
    fea = FEA3D(spec, grid)
    rho = np.ones((length, h, b))
    u_direct = fea.solve(rho, 3.0, method="direct")
    return grid, fea, rho, u_direct


def test_cantilever_vs_timoshenko(cantilever):
    grid, _, _, u = cantilever
    length, h, b = 32, 8, 8
    tip = float(np.mean([u[3 * grid.node_id(length, y, z) + 1]
                         for y in range(h + 1) for z in range(b + 1)]))
    inertia = b * h ** 3 / 12
    shear_g, kappa = 1 / 2.6, 5 / 6
    delta = -(length ** 3 / (3 * inertia) + length / (kappa * shear_g * h * b))
    assert abs((tip - delta) / delta) < 0.05  # đo thật: 2.84%


# ── CG vs direct — điểm sống còn ────────────────────────────────

def test_cg_khop_direct(cantilever):
    _, fea, rho, u_direct = cantilever
    u_cg = fea.solve(rho, 3.0, method="cg")
    rel = np.linalg.norm(u_cg - u_direct) / np.linalg.norm(u_direct)
    assert rel < 1e-6  # đo thật: 9.1e-13
    assert fea.last_cg_iters > 0


def test_warm_start_hoi_tu_tuc_thi(cantilever):
    _, fea, rho, u_direct = cantilever
    u2 = fea.solve(rho, 3.0, method="cg", x0=u_direct)
    assert fea.last_cg_iters <= 5  # đo thật: 0 vòng
    assert np.linalg.norm(u2 - u_direct) / np.linalg.norm(u_direct) < 1e-6


def test_compliance_va_clapeyron(cantilever):
    _, fea, rho, u = cantilever
    c = fea.compliance(u)
    en = fea.element_energy(u, rho, 3.0)
    assert c > 0
    assert abs(en.sum() - 0.5 * c) / c < 1e-9


# ── nhánh lỗi ───────────────────────────────────────────────────

@pytest.mark.parametrize("method", ["direct", "cg"])
def test_thieu_ngam_solver_error(tmp_path, method):
    spec = mk(tmp_path, {
        "nelx": 4, "nely": 4, "nelz": 4, "volfrac": 0.5,
        "loads": [{"x": 4, "y": 2, "z": 2, "fy": -1.0}],
        "supports": [{"x": 0, "y": 0, "z": 0, "dof": "y"}],
        "material": {"E": 1.0, "nu": 0.3},
        "simp": {"p": 3.0, "rmin": 1.4}, "preserve": [], "void": []})
    fea = FEA3D(spec, Grid3D(spec))
    with pytest.raises(SolverError):
        fea.solve(np.ones((4, 4, 4)), 3.0, method=method)


def test_sai_shape_va_method_la(cantilever):
    _, fea, rho, u = cantilever
    with pytest.raises(ValueError):
        fea.solve(rho.transpose(1, 0, 2), 3.0)
    with pytest.raises(ValueError):
        fea.solve(rho, 3.0, method="gpu")
    with pytest.raises(ValueError):
        fea.solve(rho, 3.0, method="cg", x0=np.ones(7))


def test_deterministic_direct(cantilever):
    _, fea, rho, u1 = cantilever
    u2 = fea.solve(rho, 3.0, method="direct")
    assert np.array_equal(u1, u2)
