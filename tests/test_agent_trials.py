"""Acceptance Tầng 3.3 — DoD-3.1 (spec stage3-t3).

Đọc lại bằng chứng bench/agent_trials/: 3 bài đề tiếng Việt → spec →
run → report do AGENT tự vận hành 16/07/2026 (bai1 công-xôn nhôm 47
vòng · bai2 dầm thép 2 gối 14 vòng · bai3 tấm treo titan 2 case 14
vòng). Test CHẤM LẠI ĐỘC LẬP 4 tiêu chí AGENT.md mục 4 từ report gốc
— không tin danh_gia.json nói gì (chống tự chấm tự khen, S3-R3).
"""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TRIALS = ROOT / "bench" / "agent_trials"
BAI = ["bai1", "bai2", "bai3"]


@pytest.mark.parametrize("bai", BAI)
def test_dod_3_1_du_bang_chung(bai):
    goc = TRIALS / bai
    for f in ("de_bai.txt", "spec.json", "validate.json",
              "danh_gia.json", "out/report.json"):
        assert (goc / f).is_file(), f"{bai}/{f} thiếu"


@pytest.mark.parametrize("bai", BAI)
def test_dod_3_1_cham_lai_doc_lap(bai):
    goc = TRIALS / bai
    spec = json.loads((goc / "spec.json").read_text(encoding="utf-8"))
    rep = json.loads((goc / "out/report.json").read_text(encoding="utf-8"))
    val = json.loads((goc / "validate.json").read_text(encoding="utf-8"))
    vf = spec["volfrac"]
    assert val["trang_thai"] == "HOP_LE"                      # validate 0
    assert rep["status"] == "PASS" and rep["converged"] is True
    assert abs(rep["volume_fraction"] - vf) <= 0.01 * vf
    assert rep["stl"]["watertight"] is True
    assert rep["stl"]["n_components"] == 1
    dg = json.loads((goc / "danh_gia.json").read_text(encoding="utf-8"))
    assert dg["ket_luan"] == "THANH CONG"
    assert all(dg["tieu_chi"].values())


def test_3_bai_phu_3_nhanh_khac_nhau():
    # B1 v1+face support · B2 v1+node support+vật liệu khác · B3 v2 đa
    # case + preserve/void — đúng "3 bài toán khác nhau" của hợp đồng.
    s1, s2, s3 = (json.loads((TRIALS / b / "spec.json")
                  .read_text(encoding="utf-8")) for b in BAI)
    assert "loads" in s1 and "face" in s1["supports"][0]
    assert "loads" in s2 and "x" in s2["supports"][0]
    assert "load_cases" in s3 and s3["preserve"] and s3["void"]
    assert len({s1["material_name"], s2["material_name"],
                s3["material_name"]}) == 3
