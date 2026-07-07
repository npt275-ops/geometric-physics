"""Acceptance Tầng 0.4 — DoD-0.1/0.2/0.3/0.4/0.6 (spec stage0-t4 mục 8).

Đo thật 07/07/2026: geophys c=203.1812 vs top88 port c=203.1925 (lệch 0.006%),
cùng 94 vòng; checkerboard 0; mono violation 0/93; volume 0.5000.
"""

import json
from pathlib import Path

import numpy as np
import pytest
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

from geophys.grid2d import Grid2D
from geophys.optimize import optimize
from geophys.spec_loader import load_spec

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


# ── PORT TOP88 TRUNG THỰC (Andreassen 2011) — đường đối chứng độc lập ──

def top88_ref(nelx, nely, volfrac, penal, rmin, max_it=300):
    e0, e_min, nu = 1.0, 1e-9, 0.3
    k = np.array([1/2 - nu/6, 1/8 + nu/8, -1/4 - nu/12, -1/8 + 3*nu/8,
                  -1/4 + nu/12, -1/8 - nu/8, nu/6, 1/8 - 3*nu/8])
    idx = np.array([[0, 1, 2, 3, 4, 5, 6, 7], [1, 0, 7, 6, 5, 4, 3, 2],
                    [2, 7, 0, 5, 6, 3, 4, 1], [3, 6, 5, 0, 7, 2, 1, 4],
                    [4, 5, 6, 7, 0, 1, 2, 3], [5, 4, 3, 2, 1, 0, 7, 6],
                    [6, 3, 4, 1, 2, 7, 0, 5], [7, 2, 1, 4, 3, 6, 5, 0]])
    ke = e0 / (1 - nu ** 2) * k[idx]
    nel = nelx * nely
    ndof = 2 * (nelx + 1) * (nely + 1)
    edof = np.zeros((nel, 8), dtype=int)
    for elx in range(nelx):
        for ely in range(nely):
            el = ely + elx * nely
            n1 = (nely + 1) * elx + ely
            n2 = (nely + 1) * (elx + 1) + ely
            edof[el] = [2*n1+2, 2*n1+3, 2*n2+2, 2*n2+3,
                        2*n2, 2*n2+1, 2*n1, 2*n1+1]
    i_k = np.kron(edof, np.ones((8, 1), dtype=int)).flatten()
    j_k = np.kron(edof, np.ones((1, 8), dtype=int)).flatten()
    force = np.zeros(ndof)
    force[1] = -1.0  # y node góc trên-trái (MBB nửa mô hình)
    fixed = np.union1d(np.arange(0, 2 * (nely + 1), 2), [ndof - 1])
    free = np.setdiff1d(np.arange(ndof), fixed)
    i_h, j_h, s_h = [], [], []
    reach = int(np.ceil(rmin)) - 1
    for i1 in range(nelx):
        for j1 in range(nely):
            e1 = i1 * nely + j1
            for i2 in range(max(i1 - reach, 0), min(i1 + reach + 1, nelx)):
                for j2 in range(max(j1 - reach, 0), min(j1 + reach + 1, nely)):
                    w = rmin - np.hypot(i1 - i2, j1 - j2)
                    if w > 0:
                        i_h.append(e1)
                        j_h.append(e2 := i2 * nely + j2)
                        s_h.append(w)
    h_mat = coo_matrix((s_h, (i_h, j_h)), shape=(nel, nel)).tocsr()
    h_sum = np.asarray(h_mat.sum(1)).flatten()
    x = np.full(nel, volfrac)
    change, loop, c = 1.0, 0, np.inf
    while change > 0.01 and loop < max_it:
        loop += 1
        xp = x ** penal
        s_k = ((ke.flatten()[None]).T
               * (e_min + xp * (e0 - e_min))).flatten(order="F")
        k_glob = coo_matrix((s_k, (i_k, j_k)), shape=(ndof, ndof)).tocsc()
        u = np.zeros(ndof)
        u[free] = spsolve(k_glob[free, :][:, free], force[free])
        ce = np.einsum("ij,jk,ik->i", u[edof], ke, u[edof])
        c = ((e_min + xp * (e0 - e_min)) * ce).sum()
        dc = -penal * x ** (penal - 1) * (e0 - e_min) * ce
        dc = np.asarray(h_mat @ (x * dc)).flatten() / (h_sum
                                                       * np.maximum(1e-3, x))
        l1, l2, move = 0.0, 1e9, 0.2
        while (l2 - l1) / (l1 + l2) > 1e-3:
            lmid = 0.5 * (l1 + l2)
            xnew = np.maximum(0, np.maximum(x - move, np.minimum(
                1, np.minimum(x + move,
                              x * np.sqrt(np.maximum(-dc, 0) / lmid)))))
            if xnew.sum() > volfrac * nel:
                l1 = lmid
            else:
                l2 = lmid
        change = np.abs(xnew - x).max()
        x = xnew
    return c, loop


# ── MBB benchmark — chạy MỘT lần, dùng chung cho nhiều test ─────

@pytest.fixture(scope="module")
def mbb_result():
    return optimize(load_spec(EXAMPLES / "spec_mbb_60x20.json"))


def test_dod_0_1_khop_top88(mbb_result):
    """DoD-0.1 — cửa ải Stage 0. Đo thật: lệch 0.006%."""
    c_ref, _ = top88_ref(60, 20, 0.5, 3.0, 1.5)
    assert abs(mbb_result.compliance - c_ref) / c_ref < 0.05


def test_dod_0_2_khong_checkerboard(mbb_result):
    b = (mbb_result.rho > 0.5).astype(int)
    cb = ((b[:-1, :-1] == b[1:, 1:]) & (b[1:, :-1] == b[:-1, 1:])
          & (b[:-1, :-1] != b[1:, :-1])).sum()
    assert int(cb) == 0


def test_dod_0_3_hoi_tu(mbb_result):
    assert mbb_result.converged
    assert mbb_result.n_iter < 200
    h = mbb_result.history["compliance"]
    assert all(h[i + 1] <= h[i] * 1.02 for i in range(len(h) - 1))
    assert h[-1] < h[0]


def test_cau_truc_gian_mbb(mbb_result):
    """Giàn đặc trưng: 2 thanh biên đặc + không phải khối đặc."""
    b = mbb_result.rho > 0.5
    assert b[:, 19].mean() > 0.9          # thanh biên dưới (gối → giữa nhịp)
    assert b[:30, 0].mean() > 0.9          # thanh biên trên phía tải
    assert 0.2 < b[:, 1:19].mean() < 0.8   # ruột có lỗ — không khối đặc
    assert all(b[x, :].any() for x in range(60))  # liên tục theo nhịp
    assert abs(mbb_result.rho.mean() - 0.5) < 0.005


# ── DoD-0.4: ràng buộc giữ nguyên MỌI vòng ─────────────────────

def test_dod_0_4_preserve_void_moi_vong():
    spec = load_spec(EXAMPLES / "spec_preserve_void_20x20.json")
    grid = Grid2D(spec)
    violations = []

    def watchdog(i, rho, c):
        if not (rho[grid.preserve_mask] == 1.0).all():
            violations.append(("preserve", i))
        if not (rho[grid.void_mask] == 0.0).all():
            violations.append(("void", i))

    res = optimize(spec, callback=watchdog)
    assert violations == []
    assert res.converged
    assert (res.rho[grid.preserve_mask] == 1.0).all()
    assert (res.rho[grid.void_mask] == 0.0).all()
    assert abs(res.rho.mean() - spec.volfrac) < 0.01 * spec.volfrac


# ── DoD-0.6: deterministic từng bit ─────────────────────────────

def test_dod_0_6_deterministic(tmp_path):
    data = {"nelx": 20, "nely": 10, "volfrac": 0.4,
            "loads": [{"x": 20, "y": 5, "fx": 0.0, "fy": -1.0}],
            "supports": [{"edge": "left", "dof": "both"}],
            "material": {"E": 1.0, "nu": 0.3},
            "simp": {"p": 3.0, "rmin": 1.3},
            "preserve": [], "void": []}
    f = tmp_path / "s.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    r1 = optimize(load_spec(f))
    r2 = optimize(load_spec(f))
    assert np.array_equal(r1.rho, r2.rho)
    assert r1.compliance == r2.compliance
    assert r1.n_iter == r2.n_iter


# ── log JSON ────────────────────────────────────────────────────

def test_log_json_ghi_du(tmp_path):
    spec = load_spec(EXAMPLES / "spec_preserve_void_20x20.json")
    log = tmp_path / "run.json"
    res = optimize(spec, log_path=log)
    data = json.loads(log.read_text(encoding="utf-8"))
    assert len(data["compliance"]) == res.n_iter
    assert data["compliance"][-1] == res.compliance
