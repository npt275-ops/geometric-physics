"""Acceptance Tầng 0.2 — FEA 2D Q4 (spec stage0-t2 mục 8).

Ngưỡng chốt theo số đo thật ngày 07/07/2026:
KE vs Gauss 1e-16 · patch 4.5e-15 · Timoshenko 0.75% · góc chết 14%.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from geophys.fea2d import FEA2D, SolverError, ke_q4
from geophys.grid2d import Grid2D
from geophys.spec_loader import load_spec

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def make_spec(tmp_path, data):
    f = tmp_path / "spec.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    return load_spec(f)


def solid(spec):
    return np.ones((spec.nelx, spec.nely), dtype=np.float64)


# ── KE: hai đường độc lập phải gặp nhau ─────────────────────────

def ke_gauss(e_mod, nu):
    """KE qua tích phân Gauss 2×2 — đường tính ĐỘC LẬP với module."""
    nodes = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float64)
    d_mat = e_mod / (1 - nu ** 2) * np.array(
        [[1, nu, 0], [nu, 1, 0], [0, 0, (1 - nu) / 2]])
    gp = 1 / np.sqrt(3)
    ke = np.zeros((8, 8))
    for xi in (-gp, gp):
        for eta in (-gp, gp):
            dn = 0.25 * np.array(
                [[-(1 - eta), (1 - eta), (1 + eta), -(1 + eta)],
                 [-(1 - xi), -(1 + xi), (1 + xi), (1 - xi)]])
            jac = dn @ nodes
            dnx = np.linalg.inv(jac) @ dn
            b_mat = np.zeros((3, 8))
            b_mat[0, 0::2] = dnx[0]
            b_mat[1, 1::2] = dnx[1]
            b_mat[2, 0::2] = dnx[1]
            b_mat[2, 1::2] = dnx[0]
            ke += b_mat.T @ d_mat @ b_mat * np.linalg.det(jac)
    return ke


@pytest.mark.parametrize("nu", [0.25, 0.3, 0.4])
def test_ke_giai_tich_khop_gauss(nu):
    assert np.abs(ke_q4(1.0, nu) - ke_gauss(1.0, nu)).max() < 1e-10


def test_ke_doi_xung_va_rigid_modes():
    ke = ke_q4(1.0, 0.3)
    assert np.abs(ke - ke.T).max() < 1e-14
    eig = np.linalg.eigvalsh(ke)
    assert int(np.sum(np.abs(eig) < 1e-12)) == 3  # 2 tịnh tiến + 1 xoay
    assert int(np.sum(eig > 1e-12)) == 5


# ── Patch test: kéo đều → trạng thái ứng suất đồng nhất ─────────

@pytest.fixture(scope="module")
def patch_case(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("patch")
    n = 4
    spec = make_spec(tmp, {
        "nelx": n, "nely": n, "volfrac": 0.5,
        "loads": [{"x": n, "y": y, "fx": 1.0 if 0 < y < n else 0.5,
                   "fy": 0.0} for y in range(n + 1)],
        "supports": [{"edge": "left", "dof": "x"},
                     {"x": 0, "y": n, "dof": "y"}],
        "material": {"E": 1.0, "nu": 0.3},
        "simp": {"p": 3.0, "rmin": 1.2},
        "preserve": [], "void": []})
    grid = Grid2D(spec)
    fea = FEA2D(spec, grid)
    u = fea.solve(solid(spec), 3.0)
    return spec, grid, fea, u


def test_patch_nang_luong_dong_nhat(patch_case):
    spec, _, fea, u = patch_case
    energy = fea.element_energy(u, solid(spec), 3.0)
    assert (energy.max() - energy.min()) / energy.mean() < 1e-9


def test_patch_chuyen_vi_mep_phai(patch_case):
    _, grid, _, u = patch_case
    # σ = 1 (tổng lực 4 trên cạnh cao 4), E = 1, L = 4 → ux(L) = 4
    ux_right = u[2 * np.asarray(
        [grid.node_id(4, y) for y in range(5)])]
    assert np.abs(ux_right - 4.0).max() < 1e-9


# ── Dầm console vs Timoshenko ───────────────────────────────────

def test_cantilever_vs_timoshenko(tmp_path):
    length, height, p_total = 80, 10, 1.0
    spec = make_spec(tmp_path, {
        "nelx": length, "nely": height, "volfrac": 0.5,
        "loads": [{"x": length, "y": y, "fx": 0.0,
                   "fy": -(p_total / height if 0 < y < height
                           else p_total / (2 * height))}
                  for y in range(height + 1)],
        "supports": [{"edge": "left", "dof": "both"}],
        "material": {"E": 1.0, "nu": 0.3},
        "simp": {"p": 3.0, "rmin": 1.5},
        "preserve": [], "void": []})
    grid = Grid2D(spec)
    fea = FEA2D(spec, grid)
    u = fea.solve(solid(spec), 3.0)
    tip = float(np.mean(
        [u[2 * grid.node_id(length, y) + 1] for y in range(height + 1)]))
    inertia = height ** 3 / 12
    shear_g = 1.0 / (2 * 1.3)
    kappa = 5 / 6
    delta = -(p_total * length ** 3 / (3 * inertia)
              + p_total * length / (kappa * shear_g * height))
    assert abs((tip - delta) / delta) < 0.05  # đo thật: 0.75%


# ── Static Physics Test (DoD-0.5) — khối nguyên vẹn ρ = 1 ───────

@pytest.fixture(scope="module")
def cantilever_solid():
    spec = load_spec(EXAMPLES / "spec_cantilever_40x20.json")
    grid = Grid2D(spec)
    fea = FEA2D(spec, grid)
    u = fea.solve(np.ones((40, 20)), 3.0)
    energy = fea.element_energy(u, np.ones((40, 20)), 3.0)
    return spec, grid, fea, u, energy


def test_goc_xa_gan_nhu_khong_chiu_luc(cantilever_solid):
    *_, energy = cantilever_solid
    mean_all = energy.mean()
    # lực tại giữa mép phải → 2 góc phải là vùng chết (đo thật: 14%)
    assert energy[32:40, 0:6].mean() < 0.2 * mean_all
    assert energy[32:40, 14:20].mean() < 0.2 * mean_all


def test_nang_luong_cuc_dai_tren_duong_truyen_luc(cantilever_solid):
    spec, grid, _, _, energy = cantilever_solid
    ex, ey = np.unravel_index(int(energy.argmax()), energy.shape)
    element_id = int(grid.element_id(ex, ey))
    nodes_of_max = set(grid.element_nodes[element_id].tolist())
    load_nodes = {ld.node for ld in spec.loads}
    support_nodes = {s.node for s in spec.supports}
    # cực đại phải chạm điểm đặt lực hoặc chạm ngàm
    assert nodes_of_max & (load_nodes | support_nodes)


def test_compliance_duong_va_bang_fu(cantilever_solid):
    _, _, fea, u, energy = cantilever_solid
    c = fea.compliance(u)
    assert c > 0
    # tổng năng lượng element = ½·F·U (định lý Clapeyron)
    assert abs(energy.sum() - 0.5 * c) / c < 1e-9


# ── nhánh lỗi ───────────────────────────────────────────────────

def test_thieu_ngam_raise_solver_error(tmp_path):
    spec = make_spec(tmp_path, {
        "nelx": 4, "nely": 4, "volfrac": 0.5,
        "loads": [{"x": 4, "y": 2, "fx": 0.0, "fy": -1.0}],
        "supports": [{"x": 0, "y": 4, "dof": "y"}],  # chỉ 1 dof — thiếu
        "material": {"E": 1.0, "nu": 0.3},
        "simp": {"p": 3.0, "rmin": 1.2},
        "preserve": [], "void": []})
    fea = FEA2D(spec, Grid2D(spec))
    with pytest.raises(SolverError):
        fea.solve(np.ones((4, 4)), 3.0)


def test_rho_sai_shape_raise_value_error():
    spec = load_spec(EXAMPLES / "spec_cantilever_40x20.json")
    fea = FEA2D(spec, Grid2D(spec))
    with pytest.raises(ValueError):
        fea.solve(np.ones((20, 40)), 3.0)  # đảo chiều


# ── deterministic ───────────────────────────────────────────────

def test_deterministic_tung_bit(cantilever_solid):
    spec, _, fea, u, _ = cantilever_solid
    u2 = fea.solve(np.ones((40, 20)), 3.0)
    assert np.array_equal(u, u2)
