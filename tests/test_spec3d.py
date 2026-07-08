"""Acceptance Tầng 1.1 — spec3d loader (spec stage1-t1 mục 8)."""

import json
from pathlib import Path

import pytest

from geophys.errors import SpecError
from geophys.spec3d import load_spec3d

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
ALL_3D = sorted(EXAMPLES.glob("spec3d_*.json"))


def _valid_raw() -> dict:
    return json.loads(
        (EXAMPLES / "spec3d_primitives_20.json").read_text(encoding="utf-8"))


def _dump(tmp_path, raw):
    f = tmp_path / "bad.json"
    f.write_text(json.dumps(raw), encoding="utf-8")
    return f


def test_co_3_spec_3d_mau():
    assert len(ALL_3D) == 3  # cantilever + primitives + bench 64x32x32


@pytest.mark.parametrize("path", ALL_3D, ids=lambda p: p.stem)
def test_spec_3d_parse_ok(path):
    spec = load_spec3d(path)
    assert spec.nelx >= 1 and spec.nely >= 1 and spec.nelz >= 1
    assert len(spec.loads) >= 1 and len(spec.supports) >= 1


@pytest.mark.parametrize("missing", ["nelz", "nelx", "loads", "preserve"])
def test_thieu_truong_neu_dung_ten(tmp_path, missing):
    raw = _valid_raw()
    del raw[missing]
    with pytest.raises(SpecError) as e:
        load_spec3d(_dump(tmp_path, raw))
    assert e.value.field == missing


def test_load_ngoai_luoi(tmp_path):
    raw = _valid_raw()
    raw["loads"] = [{"x": 21, "y": 0, "z": 0, "fy": -1.0}]  # x > nelx
    with pytest.raises(SpecError) as e:
        load_spec3d(_dump(tmp_path, raw))
    assert "loads[0]" in str(e.value)


def test_luc_bang_0_bi_chan(tmp_path):
    raw = _valid_raw()
    raw["loads"] = [{"x": 20, "y": 10, "z": 10, "fx": 0.0}]
    with pytest.raises(SpecError):
        load_spec3d(_dump(tmp_path, raw))


def test_face_sai_bi_chan(tmp_path):
    raw = _valid_raw()
    raw["supports"] = [{"face": "x2", "dof": "all"}]
    with pytest.raises(SpecError) as e:
        load_spec3d(_dump(tmp_path, raw))
    assert "face" in str(e.value)


def test_primitive_type_la_bi_chan(tmp_path):
    raw = _valid_raw()
    raw["void"] = [{"type": "torus", "r": 2.0}]
    with pytest.raises(SpecError) as e:
        load_spec3d(_dump(tmp_path, raw))
    assert "type" in str(e.value)


def test_primitive_thieu_truong_neu_ten(tmp_path):
    raw = _valid_raw()
    raw["void"] = [{"type": "sphere", "cx": 5.0, "cy": 5.0, "cz": 5.0}]  # thiếu r
    with pytest.raises(SpecError) as e:
        load_spec3d(_dump(tmp_path, raw))
    assert "'r'" in str(e.value)


def test_box_ngoai_luoi_bi_chan(tmp_path):
    raw = _valid_raw()
    raw["preserve"] = [{"type": "box", "x0": 0, "y0": 0, "z0": 0,
                        "x1": 20, "y1": 5, "z1": 5}]  # x1 == nelx
    with pytest.raises(SpecError):
        load_spec3d(_dump(tmp_path, raw))


def test_deterministic():
    a = load_spec3d(EXAMPLES / "spec3d_primitives_20.json")
    b = load_spec3d(EXAMPLES / "spec3d_primitives_20.json")
    assert a == b
