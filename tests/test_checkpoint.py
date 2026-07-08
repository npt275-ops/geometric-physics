"""Acceptance Tầng 1.4 — checkpoint/resume + profiling (spec stage1-t4 mục 8)."""

import json

import numpy as np
import pytest

from geophys.checkpoint import load_checkpoint, save_checkpoint, spec_digest
from geophys.optimize3d import optimize3d
from geophys.spec3d import load_spec3d

SMALL = {"nelx": 12, "nely": 6, "nelz": 4, "volfrac": 0.4,
         "loads": [{"x": 12, "y": 6, "z": 2, "fy": -1.0}],
         "supports": [{"face": "x0", "dof": "all"}],
         "material": {"E": 1.0, "nu": 0.3},
         "simp": {"p": 3.0, "rmin": 1.3}, "preserve": [], "void": []}


def mk(tmp_path, d=SMALL, name="s.json"):
    f = tmp_path / name
    f.write_text(json.dumps(d), encoding="utf-8")
    return load_spec3d(f)


# ── DoD-1.4: ngắt → resume → giống hệt chạy liền mạch ──────────

@pytest.mark.parametrize("method", ["direct", "cg"])
def test_dod_1_4_resume_giong_het(tmp_path, method):
    spec = mk(tmp_path)
    full = optimize3d(spec, method=method)
    assert full.converged and full.n_iter > 6

    ckpt = tmp_path / f"ck_{method}.npz"
    # "ngắt giữa chừng": chạy đúng nửa số vòng, checkpoint lưu tại điểm ngắt
    cut = full.n_iter // 2
    part = optimize3d(spec, method=method, max_iter=cut,
                      checkpoint_path=ckpt, checkpoint_every=1)
    assert not part.converged and part.n_iter == cut
    # resume đến hội tụ
    res = optimize3d(spec, method=method, checkpoint_path=ckpt, resume=True)
    assert res.converged
    assert res.n_iter == full.n_iter
    assert np.array_equal(res.rho, full.rho)          # GIỐNG TỪNG BIT
    assert res.compliance == full.compliance
    assert res.history["compliance"] == full.history["compliance"]


# ── Không hồi quy so với bản 1.3 ────────────────────────────────

def test_khong_tham_so_moi_van_nhu_cu(tmp_path):
    """Không dùng checkpoint ⇒ hành vi cũ (suite 1.3 cũng đang canh điều này)."""
    spec = mk(tmp_path)
    r1 = optimize3d(spec)
    r2 = optimize3d(spec)
    assert np.array_equal(r1.rho, r2.rho)
    assert r1.converged


# ── digest chặn resume nhầm bài ─────────────────────────────────

def test_digest_chan_bai_khac(tmp_path):
    spec_a = mk(tmp_path)
    other = dict(SMALL)
    other["volfrac"] = 0.5
    spec_b = mk(tmp_path, other, "s2.json")
    ckpt = tmp_path / "ck.npz"
    optimize3d(spec_a, max_iter=5, checkpoint_path=ckpt, checkpoint_every=5)
    with pytest.raises(ValueError):
        load_checkpoint(ckpt, spec_b)
    with pytest.raises(ValueError):
        optimize3d(spec_b, checkpoint_path=ckpt, resume=True)
    assert spec_digest(spec_a) != spec_digest(spec_b)


def test_resume_khong_co_file(tmp_path):
    spec = mk(tmp_path)
    with pytest.raises(FileNotFoundError):
        optimize3d(spec, checkpoint_path=tmp_path / "khong_co.npz",
                   resume=True)
    with pytest.raises(ValueError):
        optimize3d(spec, resume=True)  # thiếu checkpoint_path


# ── profiling ───────────────────────────────────────────────────

def test_profiling_du_truong(tmp_path):
    spec = mk(tmp_path)
    res = optimize3d(spec, max_iter=8)
    for key in ("t_solve", "t_grad_filter", "t_oc", "rss_mb"):
        assert len(res.history[key]) == res.n_iter
    assert all(t >= 0 for t in res.history["t_solve"])
    # psutil có trong môi trường test → rss thật
    assert max(res.history["rss_mb"]) > 0


def test_save_load_roundtrip(tmp_path):
    spec = mk(tmp_path)
    rho = np.random.default_rng(1).uniform(0.2, 0.9, (12, 6, 4))
    u = np.random.default_rng(2).normal(size=3 * 13 * 7 * 5)
    hist = {"compliance": [1.0, 0.5]}
    p = save_checkpoint(tmp_path / "ck.npz", spec, rho, u, 2, hist)
    state = load_checkpoint(p, spec)
    assert np.array_equal(state["rho"], rho)
    assert np.array_equal(state["u_prev"], u)
    assert state["n_iter"] == 2
    assert state["history"] == hist
