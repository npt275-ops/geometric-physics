"""Acceptance Tầng 0.1 — phần spec_loader (spec mục 8)."""

import json
from pathlib import Path

import pytest

from geophys.errors import SpecError
from geophys.spec_loader import load_spec

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
ALL_EXAMPLES = sorted(EXAMPLES.glob("spec_*.json"))


def _valid_raw() -> dict:
    return json.loads(
        (EXAMPLES / "spec_mbb_60x20.json").read_text(encoding="utf-8"))


# ── 3 spec mẫu parse thành công ─────────────────────────────────

def test_co_dung_3_spec_mau():
    assert len(ALL_EXAMPLES) == 3


@pytest.mark.parametrize("path", ALL_EXAMPLES, ids=lambda p: p.stem)
def test_spec_mau_parse_thanh_cong(path):
    spec = load_spec(path)
    assert spec.nelx >= 1 and spec.nely >= 1
    assert 0.0 < spec.volfrac < 1.0
    assert len(spec.loads) >= 1
    assert len(spec.supports) >= 1


# ── lỗi phải nêu đúng tên trường ────────────────────────────────

@pytest.mark.parametrize("missing", [
    "nelx", "nely", "volfrac", "loads", "supports",
    "material", "simp", "preserve", "void",
])
def test_thieu_truong_bao_dung_ten(tmp_path, missing):
    raw = _valid_raw()
    del raw[missing]
    f = tmp_path / "bad.json"
    f.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(SpecError) as exc_info:
        load_spec(f)
    assert missing in str(exc_info.value)
    assert exc_info.value.field == missing


def test_file_khong_ton_tai():
    with pytest.raises(SpecError) as exc_info:
        load_spec(ROOT / "khong_he_ton_tai.json")
    assert exc_info.value.field == "file"


def test_json_hong_bao_vi_tri(tmp_path):
    f = tmp_path / "hong.json"
    f.write_text('{"nelx": 60,,}', encoding="utf-8")
    with pytest.raises(SpecError) as exc_info:
        load_spec(f)
    assert exc_info.value.field == "json"
    assert "dòng" in str(exc_info.value)


@pytest.mark.parametrize("field,value,expect_in_msg", [
    ("nelx", -3, "nelx"),
    ("nelx", 2.5, "nelx"),
    ("volfrac", 1.5, "volfrac"),
    ("volfrac", 0.0, "volfrac"),
])
def test_gia_tri_sai_khoang(tmp_path, field, value, expect_in_msg):
    raw = _valid_raw()
    raw[field] = value
    f = tmp_path / "bad.json"
    f.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(SpecError) as exc_info:
        load_spec(f)
    assert expect_in_msg in str(exc_info.value)


def test_luc_bang_khong_bi_chan(tmp_path):
    raw = _valid_raw()
    raw["loads"] = [{"x": 0, "y": 0, "fx": 0.0, "fy": 0.0}]
    f = tmp_path / "bad.json"
    f.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(SpecError) as exc_info:
        load_spec(f)
    assert "loads[0]" in str(exc_info.value)


def test_khong_ngam_bi_chan(tmp_path):
    raw = _valid_raw()
    raw["supports"] = []
    f = tmp_path / "bad.json"
    f.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(SpecError) as exc_info:
        load_spec(f)
    assert exc_info.value.field == "supports"


def test_vung_ngoai_luoi_bi_chan(tmp_path):
    raw = _valid_raw()
    raw["preserve"] = [{"x0": 0, "y0": 0, "x1": 60, "y1": 5}]  # x1 == nelx
    f = tmp_path / "bad.json"
    f.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(SpecError) as exc_info:
        load_spec(f)
    assert "preserve[0]" in str(exc_info.value)


def test_preserve_giao_void_bi_chan(tmp_path):
    raw = _valid_raw()
    raw["preserve"] = [{"x0": 0, "y0": 0, "x1": 5, "y1": 5}]
    raw["void"] = [{"x0": 5, "y0": 5, "x1": 8, "y1": 8}]
    f = tmp_path / "bad.json"
    f.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(SpecError) as exc_info:
        load_spec(f)
    assert "preserve[0]/void[0]" in str(exc_info.value)


# ── deterministic ───────────────────────────────────────────────

def test_deterministic_hai_lan_giong_het():
    a = load_spec(EXAMPLES / "spec_mbb_60x20.json")
    b = load_spec(EXAMPLES / "spec_mbb_60x20.json")
    assert a == b
