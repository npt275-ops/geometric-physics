"""Acceptance Tầng 2.2 — vật liệu thật + đơn vị mm-N-MPa (spec stage2-t2).

Đo thật 12/07/2026: scaling E và h sai số ĐÚNG 0 (nhân đôi là exact trong
IEEE) · Timoshenko đơn vị thật 3.36% (lưới 32×8×8, h=1.25mm) · golden trùng.
"""

import json

import numpy as np
import pytest

from geophys.errors import SpecError
from geophys.fea3d import FEA3D
from geophys.grid3d import Grid3D
from geophys.materials import get_material, load_materials
from geophys.spec3d import load_spec3d


def mk(tmp_path, d, name="s.json"):
    f = tmp_path / name
    f.write_text(json.dumps(d), encoding="utf-8")
    return load_spec3d(f)


BASE = {"nelx": 8, "nely": 4, "nelz": 4, "volfrac": 0.5,
        "loads": [{"x": 8, "y": 4, "z": 2, "fy": -100.0}],
        "supports": [{"face": "x0", "dof": "all"}],
        "simp": {"p": 3.0, "rmin": 1.3}, "preserve": [], "void": []}


# ── database ────────────────────────────────────────────────────

def test_db_3_vat_lieu_va_gia_tri_hop_dong():
    db = load_materials()
    assert set(db) >= {"nhom_6061_t6", "ti_6al_4v", "thep_s235"}
    # con số 276 MPa trong DoD-2.3 phải ĐÚNG là yield nhôm 6061 trong db
    assert get_material("nhom_6061_t6")["yield_MPa"] == 276
    for m in db.values():
        assert m["E_MPa"] > 0 and 0 < m["nu"] < 0.5 and m["yield_MPa"] > 0


def test_ten_la_liet_ke_danh_sach():
    with pytest.raises(SpecError) as e:
        get_material("unobtainium")
    assert "nhom_6061_t6" in str(e.value)


def test_db_hong_bao_dung_cho(tmp_path):
    bad = tmp_path / "m.json"
    bad.write_text(json.dumps({"x": {"E_MPa": -5, "nu": 0.3,
                                     "yield_MPa": 100}}), encoding="utf-8")
    with pytest.raises(SpecError) as e:
        load_materials(bad)
    assert "E_MPa" in str(e.value)


# ── luật scaling giải tích (test cứng chống bug đơn vị S2-R2) ──

def test_scaling_E_gap_doi(tmp_path):
    rho = np.full((8, 4, 4), 0.7)
    sa = mk(tmp_path, {**BASE, "material": {"E": 70000.0, "nu": 0.33},
                       "element_size_mm": 1.0}, "a.json")
    sb = mk(tmp_path, {**BASE, "material": {"E": 140000.0, "nu": 0.33},
                       "element_size_mm": 1.0}, "b.json")
    ua = FEA3D(sa, Grid3D(sa)).solve(rho, 3.0)
    ub = FEA3D(sb, Grid3D(sb)).solve(rho, 3.0)
    assert np.allclose(ua, 2 * ub, rtol=1e-12, atol=0)  # đo: 0 bit lệch


def test_scaling_h_gap_doi(tmp_path):
    rho = np.full((8, 4, 4), 0.7)
    sa = mk(tmp_path, {**BASE, "material": {"E": 70000.0, "nu": 0.33},
                       "element_size_mm": 1.0}, "a.json")
    sc = mk(tmp_path, {**BASE, "material": {"E": 70000.0, "nu": 0.33},
                       "element_size_mm": 2.0}, "c.json")
    assert sc.E == 140000.0  # E_engine = E_MPa × h
    ua = FEA3D(sa, Grid3D(sa)).solve(rho, 3.0)
    uc = FEA3D(sc, Grid3D(sc)).solve(rho, 3.0)
    assert np.allclose(ua, 2 * uc, rtol=1e-12, atol=0)


# ── đơn vị tuyệt đối: dầm nhôm thật vs Timoshenko [mm] ─────────

def test_timoshenko_don_vi_that(tmp_path):
    l_e, h_e, b_e, h = 32, 8, 8, 1.25  # → dầm 40×10×10 mm
    loads = []
    for y in range(h_e + 1):
        for z in range(b_e + 1):
            w = ((0.5 if y in (0, h_e) else 1.0)
                 * (0.5 if z in (0, b_e) else 1.0))
            loads.append({"x": l_e, "y": y, "z": z,
                          "fy": -100.0 * w / (h_e * b_e)})
    spec = mk(tmp_path, {
        "nelx": l_e, "nely": h_e, "nelz": b_e, "volfrac": 0.5,
        "loads": loads, "supports": [{"face": "x0", "dof": "all"}],
        "material_name": "nhom_6061_t6", "element_size_mm": h,
        "simp": {"p": 3.0, "rmin": 1.5}, "preserve": [], "void": []})
    assert spec.e_mpa == 68900.0 and spec.yield_mpa == 276.0
    grid = Grid3D(spec)
    fea = FEA3D(spec, grid)
    u = fea.solve(np.ones((l_e, h_e, b_e)), 3.0)
    tip_mm = float(np.mean(
        [u[3 * grid.node_id(l_e, y, z) + 1]
         for y in range(h_e + 1) for z in range(b_e + 1)]))
    length, hs, bs = 40.0, 10.0, 10.0
    e_mod, nu, p_tot = 68900.0, 0.33, 100.0
    inertia = bs * hs ** 3 / 12
    shear_g = e_mod / (2 * (1 + nu))
    delta = -(p_tot * length ** 3 / (3 * e_mod * inertia)
              + p_tot * length / (5 / 6 * shear_g * hs * bs))
    assert abs((tip_mm - delta) / delta) < 0.05  # đo thật: 3.36%


# ── legacy không đổi hành vi ────────────────────────────────────

def test_legacy_mac_dinh(tmp_path):
    spec = mk(tmp_path, {**BASE, "material": {"E": 1.0, "nu": 0.3}})
    assert spec.element_size_mm == 1.0
    assert spec.E == 1.0 and spec.e_mpa == 1.0
    assert spec.material_name == "" and spec.yield_mpa == 0.0


# ── nhánh lỗi schema ────────────────────────────────────────────

def test_xor_material(tmp_path):
    with pytest.raises(SpecError):
        mk(tmp_path, {**BASE, "material": {"E": 1.0, "nu": 0.3},
                      "material_name": "thep_s235"})
    d = dict(BASE)
    with pytest.raises(SpecError) as e:
        mk(tmp_path, d)  # thiếu cả hai
    assert "material" in str(e.value)


def test_element_size_khong_hop_le(tmp_path):
    for bad in (0.0, -1.5):
        with pytest.raises(SpecError) as e:
            mk(tmp_path, {**BASE, "material": {"E": 1.0, "nu": 0.3},
                          "element_size_mm": bad})
        assert "element_size_mm" in str(e.value)


def test_material_name_la(tmp_path):
    with pytest.raises(SpecError) as e:
        mk(tmp_path, {**BASE, "material_name": "vibranium"})
    assert "material_name" in str(e.value)
