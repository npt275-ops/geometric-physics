"""Acceptance Tầng 3.6 — GP GAUNTLET (spec stage3-t6, đăng ký trước
commit dddfa66). Chấm lại ĐỘC LẬP từ bằng chứng gốc bench/gauntlet/
theo đúng kỳ vọng mục 4 của spec — không tin cham_diem.json.

Đo 16/07/2026: 9/10 ĐẠT; bài 08 LỆCH trung thực (OC dao động khi
preserve ~89% ngân sách — engine FAIL exit 1 tử tế); bài 09 bắt được
bug resume-tại-chỗ (đã vá + test hồi quy trong test_cli)."""

import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
G = ROOT / "bench" / "gauntlet"


def _rho(bai, out="out"):
    with np.load(G / bai / out / "checkpoint.npz") as d:
        return d["rho"].copy()


def _rep(bai, out="out"):
    return json.loads((G / bai / out / "report.json")
                      .read_text(encoding="utf-8"))


def _chung(bai):
    r = _rep(bai)
    ten = "spec_v3.json" if bai == "bai10" else "spec.json"  # bai10: spec cuối sau 3 vòng sửa
    vf = json.loads((G / bai / ten).read_text(encoding="utf-8"))["volfrac"]
    assert r["status"] == "PASS" and r["converged"] is True
    assert abs(r["volume_fraction"] - vf) <= 0.01 * vf
    assert r["stl"]["watertight"] and r["stl"]["n_components"] == 1


@pytest.mark.parametrize("bai", ["bai01", "bai02", "bai03", "bai04",
                                 "bai05", "bai06", "bai07", "bai10"])
def test_tieu_chi_chung(bai):
    _chung(bai)


def test_01_bat_doi_xung_z():
    r = _rho("bai01")
    a, b = r[:, :, :3].mean(), r[:, :, 3:].mean()
    assert (a - b) / b > 0.02  # đo thật: 3.92


def test_02_don_ve_goi_gan_luc():
    r = _rho("bai02")
    a, b = r[:16].mean(), r[16:].mean()
    assert (a - b) / b > 0.05  # đo thật: 0.38


def test_03_cot_giua_dac():
    r = _rho("bai03")
    assert r[2:6, :, 2:6].mean() >= r.mean()  # đo thật: 0.986 vs 0.300


def test_05_void_tuyet_doi_vanh_nguyen():
    r = _rho("bai05")
    assert r[8:16, 8:16, :].max() == 0.0
    vanh = np.concatenate([r[2:7, 9:11, :].ravel(), r[2:7, 14:16, :].ravel(),
                           r[2:3, 11:14, :].ravel(), r[6:7, 11:14, :].ravel()])
    assert vanh.min() == 1.0


def test_06_multi_cung_hon_duoi_tai_ngang():
    from geophys.fea3d import FEA3D
    from geophys.grid3d import Grid3D
    from geophys.spec3d import load_spec3d
    spec = load_spec3d(G / "bai06" / "spec.json")
    fea = FEA3D(spec, Grid3D(spec))
    f3 = fea.forces[2]

    def c3(r):
        return fea.compliance(fea.solve(r, 3.0, force=f3), force=f3)

    ty_so = c3(_rho("bai06", "out_single")) / c3(_rho("bai06"))
    assert ty_so > 1.0  # đo thật: 2.365


def test_08_lech_trung_thuc_va_validator_chan_vuot():
    r = _rep("bai08")  # LỆCH kỳ vọng — nhưng phải LỆCH ĐÚNG KIỂU:
    assert r["status"] == "FAIL" and r["converged"] is False
    assert r["n_iter"] == 200  # chạy hết, không crash
    assert abs(r["volume_fraction"] - 0.42) <= 0.0042  # volume vẫn giữ
    v = json.loads((G / "bai08" / "validate_vuot.json")
                   .read_text(encoding="utf-8"))
    assert v["loi"][0]["ma"] == "GP-E-PHYSICS"  # biến thể vượt bị chặn


def test_09_vong_doi_fail_resume():
    truoc = _rep("bai09", "out2")  # bản resume-sang-dir-khác cũng PASS
    sau = _rep("bai09")
    assert sau["status"] == "PASS" and sau["n_iter"] > 5
    assert truoc["status"] == "PASS"


def test_10_tu_sua_3_vong():
    vs = json.loads((G / "bai10" / "vong_sua.json").read_text(encoding="utf-8"))
    assert vs["so_vong_sua"] <= 3
    ma = [l[0] for v in vs["nhat_ky"] for l in v["loi"]]
    assert ma == ["GP-E-PHYSICS", "GP-E-GEOMETRY"]  # đúng 2 lỗi gieo
    assert _rep("bai10")["status"] == "PASS"
