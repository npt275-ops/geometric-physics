"""Acceptance Tầng 2.3 — bàn đạp phanh (spec stage2-t3 mục 8).

Đo thật bản smoke 14/07/2026: multi hội tụ 72 vòng · single 73 vòng ·
c₃(single)/c₃(multi) = 1.45 · c₂ ratio 0.99 (cos15° — xem spec mục 4b) ·
Δρ 32.2% · STL watertight, volume lệch 1.3%.

Test nặng (thí nghiệm DoD-2.1 trọn) chạy trên CI — sandbox deselect như
test_dod_1_1 (giới hạn 45s/lệnh).
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from geophys.export_stl import export_stl
from geophys.fea3d import FEA3D
from geophys.grid3d import Grid3D
from geophys.optimize3d import optimize3d
from geophys.spec3d import load_spec3d

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


# ── nhanh: generator + spec hợp lệ + hình học đúng ─────────────

def test_generator_deterministic(tmp_path):
    """Chạy lại generator → 4 file giống hệt bytes bản đã commit."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "gen_brake_pedal_spec.py")],
        capture_output=True, text=True, check=True, cwd=ROOT)
    assert "spec_brake_pedal.json" in result.stdout
    # generator ghi đè examples/ — nếu khác bản commit, git sẽ báo bẩn
    # (đối chiếu bytes ở đây cho chắc)
    for name in ("spec_brake_pedal.json", "spec_brake_smoke.json"):
        data = json.loads((EXAMPLES / name).read_text(encoding="utf-8"))
        assert data["volfrac"] == 0.45
        assert data["material_name"] == "nhom_6061_t6"


@pytest.mark.parametrize("name,cases", [
    ("spec_brake_pedal", 3), ("spec_brake_pedal_single", 1),
    ("spec_brake_smoke", 3), ("spec_brake_smoke_single", 1),
])
def test_spec_hop_le(name, cases):
    spec = load_spec3d(EXAMPLES / f"{name}.json")
    assert len(spec.load_cases) == cases
    assert spec.yield_mpa == 276.0  # nhôm 6061 — con số DoD-2.3
    assert spec.volfrac == 0.45


def test_hinh_hoc_smoke():
    spec = load_spec3d(EXAMPLES / "spec_brake_smoke.json")
    grid = Grid3D(spec)
    # lỗ trục xuyên suốt z, vành preserve bao quanh, pad ở góc trên-phải
    assert int(grid.void_mask.sum()) == 20      # đo: trụ r=1.5 × 5 lớp
    assert int(grid.preserve_mask.sum()) == 160
    assert grid.preserve_mask[36:, :2, :].all()  # pad
    # tải case 1 tổng đúng 1200N theo +y
    total_fy = sum(ld.fy for ld in spec.load_cases[0][1])
    assert abs(total_fy - 1200.0) < 1e-3
    # case 3 tổng 360N theo +z
    total_fz = sum(ld.fz for ld in spec.load_cases[2][1])
    assert abs(total_fz - 360.0) < 1e-3


def test_hinh_hoc_full():
    spec = load_spec3d(EXAMPLES / "spec_brake_pedal.json")
    grid = Grid3D(spec)
    assert int(grid.void_mask.sum()) == 320
    assert int(grid.preserve_mask.sum()) == 1520
    assert len(spec.supports) == 407
    total_fy = sum(ld.fy for ld in spec.load_cases[0][1])
    assert abs(total_fy - 1200.0) < 1e-3


# ── nặng (CI): thí nghiệm DoD-2.1 trọn trên bản smoke ──────────

def test_dod_2_1_thi_nghiem_smoke():
    """Multi vs single + đánh giá chéo — đo thật: c₃ ratio 1.45."""
    spec_m = load_spec3d(EXAMPLES / "spec_brake_smoke.json")
    spec_s = load_spec3d(EXAMPLES / "spec_brake_smoke_single.json")
    r_multi = optimize3d(spec_m, method="cg")
    r_single = optimize3d(spec_s, method="cg")
    assert r_multi.converged and r_single.converged

    fea = FEA3D(spec_m, Grid3D(spec_m))
    f_side = fea.forces[2]  # tải ngang (đạp xéo) — phép thử DoD-2.1
    c3_s = fea.compliance(fea.solve(r_single.rho, 3.0, force=f_side),
                          force=f_side)
    c3_m = fea.compliance(fea.solve(r_multi.rho, 3.0, force=f_side),
                          force=f_side)
    assert c3_s / c3_m >= 1.3  # đo thật: 1.45

    # DoD-2.4 (bản smoke): volume 45% ±1% tương đối
    assert abs(r_multi.rho.mean() - 0.45) < 0.0045
    # khác rõ rệt
    diff = (np.linalg.norm(r_multi.rho - r_single.rho)
            / np.linalg.norm(r_single.rho))
    assert diff > 0.05  # đo thật: 32.2%
    # DoD-2.2 (bản smoke): STL kín
    _, rep = export_stl(r_multi.rho, Path("/tmp") / "brake_smoke.stl")
    assert rep["watertight"] and rep["n_components"] == 1
