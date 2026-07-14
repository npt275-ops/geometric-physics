"""Acceptance Tầng 2.1 — multi-load (spec stage2-t1 mục 8).

GOLDEN VALUES chụp bằng code TRƯỚC refactor (12/07/2026) — cửa sinh tử:
code mới chạy spec v1 phải tái tạo ĐÚNG TỪNG BIT. Đo sau refactor:
golden khớp ✓ · FD multi 1.27e-05 · multi vs single 77.4% · resume ✓.
"""

import hashlib
import json

import numpy as np
import pytest

from geophys.errors import SpecError
from geophys.fea3d import FEA3D
from geophys.grid3d import Grid3D
from geophys.optimize3d import optimize3d
from geophys.sensitivity3d import dc_drho
from geophys.spec3d import load_spec3d

# ── golden constants (KHÔNG BAO GIỜ sửa trừ khi có nghi thức mở khóa) ──
G1_SPEC = {"nelx": 12, "nely": 6, "nelz": 4, "volfrac": 0.4,
           "loads": [{"x": 12, "y": 6, "z": 2, "fy": -1.0}],
           "supports": [{"face": "x0", "dof": "all"}],
           "material": {"E": 1.0, "nu": 0.3},
           "simp": {"p": 3.0, "rmin": 1.3}, "preserve": [], "void": []}
G1_ITER = 26
G1_C = 28.964919725332997
G1_HASH = "e9167fb4797180f62b0745e3d3ca04e5cf2810b0857267fcaad288e64a57b23d"

G2_SPEC = {"nelx": 10, "nely": 10, "nelz": 6, "volfrac": 0.35,
           "loads": [{"x": 10, "y": 5, "z": 3, "fy": -1.0},
                     {"x": 10, "y": 10, "z": 3, "fx": 0.5}],
           "supports": [{"face": "x0", "dof": "all"}],
           "material": {"E": 1.0, "nu": 0.3},
           "simp": {"p": 3.0, "rmin": 1.4},
           "preserve": [{"type": "box", "x0": 0, "y0": 0, "z0": 0,
                         "x1": 0, "y1": 9, "z1": 5}],
           "void": [{"type": "sphere", "cx": 5.0, "cy": 3.0, "cz": 3.0,
                     "r": 1.5}]}
G2_ITER = 27
G2_C = 10.079410389351352
G2_HASH = "9ff77ed18f7b9ed821128a65b31bde5674c81416aaa938e4548c8dee438e2330"

L1 = [{"x": 12, "y": 6, "z": 2, "fy": -1.0}]
L2 = [{"x": 12, "y": 3, "z": 4, "fz": 1.0}]


def mk(tmp_path, d, name="s.json"):
    f = tmp_path / name
    f.write_text(json.dumps(d), encoding="utf-8")
    return load_spec3d(f)


def base(**override):
    d = {"nelx": 12, "nely": 6, "nelz": 4, "volfrac": 0.4,
         "supports": [{"face": "x0", "dof": "all"}],
         "material": {"E": 1.0, "nu": 0.3},
         "simp": {"p": 3.0, "rmin": 1.3}, "preserve": [], "void": []}
    d.update(override)
    return d


# ── HỒI QUY GOLDEN — cửa sinh tử của tầng 2.1 ──────────────────

def test_golden_g1_direct(tmp_path):
    res = optimize3d(mk(tmp_path, G1_SPEC))
    assert res.n_iter == G1_ITER
    assert res.compliance == G1_C
    assert hashlib.sha256(res.rho.tobytes()).hexdigest() == G1_HASH


def test_golden_g2_cg_preserve_void(tmp_path):
    res = optimize3d(mk(tmp_path, G2_SPEC), method="cg")
    assert res.n_iter == G2_ITER
    assert res.compliance == G2_C
    assert hashlib.sha256(res.rho.tobytes()).hexdigest() == G2_HASH


# ── tương đương v1 ↔ v2 một case ────────────────────────────────

def test_v1_v2_mot_case_trung_bit(tmp_path):
    r1 = optimize3d(mk(tmp_path, base(loads=L1), "v1.json"))
    r2 = optimize3d(mk(tmp_path, base(
        load_cases=[{"weight": 1.0, "loads": L1}]), "v2.json"))
    assert np.array_equal(r1.rho, r2.rho)
    assert r1.compliance == r2.compliance
    assert r1.n_iter == r2.n_iter


# ── FD check multi-load ─────────────────────────────────────────

def test_fd_check_multi(tmp_path):
    spec = mk(tmp_path, base(load_cases=[
        {"weight": 0.7, "loads": L1}, {"weight": 0.3, "loads": L2}]))
    grid = Grid3D(spec)
    fea = FEA3D(spec, grid)
    rng = np.random.default_rng(42)
    rho = rng.uniform(0.3, 0.9, (12, 6, 4))

    def total_c(r):
        return sum(w * fea.compliance(fea.solve(r, 3.0, force=f), force=f)
                   for w, f in zip(fea.weights, fea.forces))

    dc = None
    for w, f in zip(fea.weights, fea.forces):
        u = fea.solve(rho, 3.0, force=f)
        d = w * dc_drho(fea, u, rho, 3.0)
        dc = d if dc is None else dc + d
    h = 1e-6
    for idx in rng.choice(288, 10, replace=False):
        e = np.unravel_index(int(idx), (12, 6, 4))
        rp = rho.copy()
        rp[e] += h
        rm = rho.copy()
        rm[e] -= h
        fd = (total_c(rp) - total_c(rm)) / (2 * h)
        assert abs((dc[e] - fd) / fd) < 0.01  # đo thật: 1.27e-05


# ── multi-load THẬT SỰ đổi cấu trúc ─────────────────────────────

def test_multi_khac_single_dinh_luong(tmp_path):
    r_single = optimize3d(mk(tmp_path, base(loads=L1), "s.json"))
    r_multi = optimize3d(mk(tmp_path, base(load_cases=[
        {"weight": 0.7, "loads": L1},
        {"weight": 0.3, "loads": L2}]), "m.json"))
    assert r_multi.converged
    diff = (np.linalg.norm(r_multi.rho - r_single.rho)
            / np.linalg.norm(r_single.rho))
    assert diff > 0.05  # đo thật: 77.4%
    # volume vẫn đúng ràng buộc
    assert abs(r_multi.rho.mean() - 0.4) < 0.004
    # history có compliance từng case
    assert len(r_multi.history["c_cases"][-1]) == 2


# ── checkpoint/resume với multi-case ────────────────────────────

def test_checkpoint_resume_multi_case(tmp_path):
    spec = mk(tmp_path, base(load_cases=[
        {"weight": 0.7, "loads": L1}, {"weight": 0.3, "loads": L2}]))
    full = optimize3d(spec)
    ckpt = tmp_path / "ck.npz"
    cut = full.n_iter // 2
    optimize3d(spec, max_iter=cut, checkpoint_path=ckpt, checkpoint_every=1)
    res = optimize3d(spec, checkpoint_path=ckpt, resume=True)
    assert res.n_iter == full.n_iter
    assert np.array_equal(res.rho, full.rho)
    assert res.compliance == full.compliance


# ── nhánh lỗi schema v2 ─────────────────────────────────────────

@pytest.mark.parametrize("bad,expect", [
    ({"load_cases": []}, "load_cases"),
    ({"load_cases": [{"weight": 0.0, "loads": [{"x": 1, "y": 1, "z": 1,
                                                "fy": -1.0}]}]}, "weight"),
    ({"load_cases": [{"weight": -1, "loads": [{"x": 1, "y": 1, "z": 1,
                                               "fy": -1.0}]}]}, "weight"),
    ({"load_cases": [{"weight": 1.0}]}, "load_cases[0]"),
])
def test_schema_v2_loi(tmp_path, bad, expect):
    with pytest.raises(SpecError) as e:
        mk(tmp_path, base(**bad))
    assert expect in str(e.value)


def test_ca_hai_hoac_khong_cai_nao(tmp_path):
    with pytest.raises(SpecError):
        mk(tmp_path, base(loads=L1,
                          load_cases=[{"weight": 1.0, "loads": L2}]))
    with pytest.raises(SpecError) as e:
        mk(tmp_path, base())
    assert "loads" in str(e.value)


def test_force_sai_shape(tmp_path):
    spec = mk(tmp_path, base(loads=L1))
    fea = FEA3D(spec, Grid3D(spec))
    with pytest.raises(ValueError):
        fea.solve(np.ones((12, 6, 4)), 3.0, force=np.ones(7))
