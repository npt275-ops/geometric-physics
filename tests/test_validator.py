"""Acceptance Tầng 3.1 — Spec Validator (spec stage3-t1, DoD-3.2).

10 spec cố tình sai (đúng lời hợp đồng: "thiếu ngàm, lực = 0, vùng bảo
tồn ngoài lưới, volume target > 1...") — validator phải bắt 10/10 với
lỗi actionable {ma, vi_tri, ly_do, goi_y}, KHÔNG raise, KHÔNG traceback.
"""

import json
from pathlib import Path

import pytest

from geophys.validate import validate_spec

ROOT = Path(__file__).resolve().parents[1]

GOC = {"nelx": 8, "nely": 4, "nelz": 4, "volfrac": 0.4,
       "loads": [{"x": 8, "y": 4, "z": 2, "fy": -100.0}],
       "supports": [{"face": "x0", "dof": "all"}],
       "material_name": "nhom_6061_t6", "element_size_mm": 2.0,
       "simp": {"p": 3.0, "rmin": 1.3}, "preserve": [], "void": []}


def _viet(tmp_path, spec, ten="spec.json"):
    p = tmp_path / ten
    p.write_text(json.dumps(spec), encoding="utf-8")
    return p


def _sua(**doi):
    s = json.loads(json.dumps(GOC))
    s.update(doi)
    return s


# ── 10 SPEC RÁC (DoD-3.2) — (tên, spec hoặc None=file đặc biệt, mã) ──
RAC = [
    ("thieu_ngam", _sua(supports=[]), "GP-E-PHYSICS"),
    ("luc_bang_0", _sua(loads=[{"x": 8, "y": 4, "z": 2, "fy": 0.0}]),
     "GP-E-PHYSICS"),
    ("preserve_ngoai_luoi", _sua(preserve=[
        {"type": "box", "x0": 90, "y0": 0, "z0": 0,
         "x1": 95, "y1": 3, "z1": 3}]), "GP-E-GEOMETRY"),
    ("volfrac_qua_1", _sua(volfrac=1.5), "GP-E-PHYSICS"),
    ("thieu_truong_nelx", {k: v for k, v in GOC.items() if k != "nelx"},
     "GP-E-SCHEMA"),
    ("vat_lieu_khong_ton_tai", _sua(material_name="unobtainium"),
     "GP-E-SCHEMA"),
    ("preserve_giao_void",
     _sua(preserve=[{"type": "box", "x0": 0, "y0": 0, "z0": 0,
                     "x1": 3, "y1": 3, "z1": 3}],
          void=[{"type": "box", "x0": 2, "y0": 0, "z0": 0,
                 "x1": 5, "y1": 3, "z1": 3}]), "GP-E-GEOMETRY"),
    ("tai_ngoai_luoi", _sua(loads=[{"x": 99, "y": 4, "z": 2,
                                    "fy": -100.0}]), "GP-E-PHYSICS"),
    ("preserve_vuot_volfrac",
     _sua(volfrac=0.1, preserve=[{"type": "box", "x0": 0, "y0": 0,
                                  "z0": 0, "x1": 7, "y1": 3, "z1": 3}]),
     "GP-E-PHYSICS"),
    # json_hong xử riêng bên dưới (không phải dict hợp lệ)
]


@pytest.mark.parametrize("ten,spec,ma", RAC, ids=[r[0] for r in RAC])
def test_dod_3_2_bat_rac(tmp_path, ten, spec, ma):
    kq = validate_spec(_viet(tmp_path, spec))
    assert kq["trang_thai"] == "KHONG_HOP_LE", ten
    assert kq["loi"], ten
    assert any(l["ma"] == ma for l in kq["loi"]), (ten, kq["loi"])
    for l in kq["loi"]:  # actionable: đủ 4 trường, gợi ý không rỗng
        assert l["ma"] and l["vi_tri"] and l["ly_do"] and l["goi_y"]


def test_dod_3_2_json_hong(tmp_path):
    p = tmp_path / "hong.json"
    p.write_text('{"nelx": 8,,,', encoding="utf-8")
    kq = validate_spec(p)
    assert kq["trang_thai"] == "KHONG_HOP_LE"
    assert kq["loi"][0]["ma"] == "GP-E-JSON"


def test_file_khong_ton_tai(tmp_path):
    kq = validate_spec(tmp_path / "khong_co.json")
    assert kq["loi"][0]["ma"] == "GP-E-FILE"


def test_spec_chuan_hop_le():
    kq = validate_spec(ROOT / "examples" / "spec_brake_smoke.json")
    assert kq["trang_thai"] == "HOP_LE" and kq["loi"] == []
    assert kq["tom_tat"]["so_case"] == 3
    assert kq["tom_tat"]["vat_lieu"] == "nhom_6061_t6"


def test_khong_raise_voi_rac(tmp_path):
    # hợp đồng mục 7: rác → dict, không exception
    for _, spec, _ma in RAC:
        validate_spec(_viet(tmp_path, spec))
