"""Acceptance CLI — run (Tầng 2.4, DoD-2.5) + validate/report (Tầng 3.2).

Đo thật 14/07/2026: exit codes 0/1/2 đúng cả 4 nhánh; outdir đủ 7 file;
resume lần hai tức thì (resume-sau-hội-tụ được công nhận).
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

TINY = {"nelx": 10, "nely": 5, "nelz": 4, "volfrac": 0.4,
        "loads": [{"x": 10, "y": 5, "z": 2, "fy": -100.0}],
        "supports": [{"face": "x0", "dof": "all"}],
        "material_name": "nhom_6061_t6", "element_size_mm": 2.0,
        "simp": {"p": 3.0, "rmin": 1.3}, "preserve": [], "void": []}


def cli(*args, timeout=120):
    return subprocess.run([sys.executable, "-m", "geophys", *args],
                          capture_output=True, text=True, cwd=ROOT,
                          timeout=timeout)


@pytest.fixture(scope="module")
def tiny_run(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("cli")
    spec = tmp / "tiny.json"
    spec.write_text(json.dumps(TINY), encoding="utf-8")
    out = tmp / "out"
    result = cli("run", str(spec), "--outdir", str(out))
    return spec, out, result


def test_dod_2_5_mot_lenh_tron_pipeline(tiny_run):
    spec, out, result = tiny_run
    assert result.returncode == 0, result.stderr
    for f in ("checkpoint.npz", "optimize_log.json", "tiny.stl",
              "tiny_iso.png", "tiny_viewer.html", "report.json",
              "report.md"):
        assert (out / f).is_file(), f
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    assert report["converged"] is True
    assert report["material"] == "nhom_6061_t6"
    assert report["yield_mpa"] == 276.0
    assert report["stl"]["watertight"] is True
    assert 0 < report["volume_fraction"] < 1
    assert len(report["digest"]) == 64


def test_resume_lan_hai_van_pass(tiny_run):
    spec, out, _ = tiny_run
    result = cli("run", str(spec), "--outdir", str(out), timeout=60)
    assert result.returncode == 0, result.stderr  # resume-sau-hội-tụ OK


def test_spec_hong_exit_2(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"nelx": 4}', encoding="utf-8")
    result = cli("run", str(bad))
    assert result.returncode == 2
    assert "SPEC" in result.stderr or "spec" in result.stderr


def test_max_iter_thap_exit_1(tmp_path):
    spec = tmp_path / "t.json"
    spec.write_text(json.dumps(TINY), encoding="utf-8")
    result = cli("run", str(spec), "--outdir", str(tmp_path / "o"),
                 "--max-iter", "3")
    assert result.returncode == 1
    # report vẫn được ghi dù FAIL — hợp đồng "không nuốt"
    report = json.loads(
        (tmp_path / "o" / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "FAIL" and report["converged"] is False


# ── Stage 3 (Tầng 3.2): validate + report mở chính thức ──────────

def test_validate_spec_chuan_exit_0(tmp_path):
    spec = tmp_path / "t.json"
    spec.write_text(json.dumps(TINY), encoding="utf-8")
    result = cli("validate", str(spec))
    assert result.returncode == 0
    kq = json.loads(result.stdout)
    assert kq["trang_thai"] == "HOP_LE"


def test_validate_rac_exit_2_json_loi(tmp_path):
    hong = dict(TINY)
    hong["supports"] = []
    spec = tmp_path / "r.json"
    spec.write_text(json.dumps(hong), encoding="utf-8")
    result = cli("validate", str(spec))
    assert result.returncode == 2
    kq = json.loads(result.stdout)  # lỗi vẫn là JSON máy đọc được
    assert kq["loi"][0]["ma"] == "GP-E-PHYSICS"
    assert kq["loi"][0]["goi_y"]


def test_report_sau_run_exit_0(tiny_run):
    _, out, _ = tiny_run
    result = cli("report", str(out))
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["status"] == "PASS" and report["stl"]["watertight"]


def test_report_thieu_outdir_exit_2(tmp_path):
    result = cli("report", str(tmp_path / "khong_co"))
    assert result.returncode == 2


def test_lenh_la_exit_2():
    result = cli("turbo")
    assert result.returncode == 2


def test_tham_so_la_exit_2():
    result = cli("run", "x.json", "--turbo", "9000")
    assert result.returncode == 2
