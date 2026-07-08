"""Acceptance Tầng 1.3 — optimize 3D + benchmark (spec stage1-t3 mục 8).

Đo thật 08/07/2026: FD 3D 1.8e-07 · filter3d vs ref 1.8e-15 · 1 solve
benchmark (19215 dof) 0.68s.
"""

import json
from pathlib import Path

import numpy as np
import pytest
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

from geophys.fea3d import FEA3D, _ke_quadrature
from geophys.filter3d import SensitivityFilter3D
from geophys.grid3d import Grid3D
from geophys.optimize3d import optimize3d
from geophys.sensitivity3d import dc_drho, dv_drho
from geophys.spec3d import load_spec3d

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def mk(tmp_path, d):
    f = tmp_path / "s.json"
    f.write_text(json.dumps(d), encoding="utf-8")
    return load_spec3d(f)


# ── FD check — phép kiểm quan trọng nhất, bản 3D ────────────────

def test_fd_check_3d(tmp_path):
    spec = mk(tmp_path, {
        "nelx": 6, "nely": 4, "nelz": 4, "volfrac": 0.5,
        "loads": [{"x": 6, "y": 2, "z": 2, "fy": -1.0}],
        "supports": [{"face": "x0", "dof": "all"}],
        "material": {"E": 1.0, "nu": 0.3},
        "simp": {"p": 3.0, "rmin": 1.4}, "preserve": [], "void": []})
    grid = Grid3D(spec)
    fea = FEA3D(spec, grid)
    rng = np.random.default_rng(42)
    rho = rng.uniform(0.3, 0.9, (6, 4, 4))
    u = fea.solve(rho, 3.0)
    dc = dc_drho(fea, u, rho, 3.0)
    assert (dc <= 0).all()
    h = 1e-6
    for idx in rng.choice(96, 12, replace=False):
        ex, ey, ez = np.unravel_index(int(idx), (6, 4, 4))
        rp = rho.copy()
        rp[ex, ey, ez] += h
        rm = rho.copy()
        rm[ex, ey, ez] -= h
        fd = (fea.compliance(fea.solve(rp, 3.0))
              - fea.compliance(fea.solve(rm, 3.0))) / (2 * h)
        assert abs((dc[ex, ey, ez] - fd) / fd) < 0.01  # đo thật: 1.8e-07


# ── Filter 3D ───────────────────────────────────────────────────

def reference_filter3d(rho, dc, rmin):
    nx, ny, nz = rho.shape
    out = np.zeros_like(rho)
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                num = wsum = 0.0
                for i2 in range(nx):
                    for j2 in range(ny):
                        for k2 in range(nz):
                            w = max(0.0, rmin - np.sqrt(
                                (i - i2) ** 2 + (j - j2) ** 2 + (k - k2) ** 2))
                            num += w * rho[i2, j2, k2] * dc[i2, j2, k2]
                            wsum += w
                out[i, j, k] = num / (wsum * max(rho[i, j, k], 1e-3))
    return out


def test_filter3d_khop_reference():
    rng = np.random.default_rng(7)
    rho = rng.uniform(0.1, 1.0, (6, 5, 4))
    dc = -rng.uniform(0.1, 5.0, (6, 5, 4))
    fast = SensitivityFilter3D(6, 5, 4, 1.9).apply(rho, dc)
    assert np.abs(fast - reference_filter3d(rho, dc, 1.9)).max() < 1e-12


def test_filter3d_truong_hang_va_checkerboard():
    filt = SensitivityFilter3D(8, 8, 6, 1.5)
    const = filt.apply(np.full((8, 8, 6), 0.5), np.full((8, 8, 6), -2.0))
    assert np.abs(const + 2.0).max() < 1e-12
    cb = (np.indices((8, 8, 6)).sum(0) % 2) * 2.0 - 1.0
    out = filt.apply(np.full((8, 8, 6), 0.5), cb)
    assert np.abs(out).max() < 0.5


# ── Vòng lặp nhỏ: hội tụ, ràng buộc, deterministic ─────────────

def test_vong_lap_nho_va_deterministic(tmp_path):
    spec = mk(tmp_path, {
        "nelx": 12, "nely": 6, "nelz": 4, "volfrac": 0.4,
        "loads": [{"x": 12, "y": 6, "z": 2, "fy": -1.0}],
        "supports": [{"face": "x0", "dof": "all"}],
        "material": {"E": 1.0, "nu": 0.3},
        "simp": {"p": 3.0, "rmin": 1.3}, "preserve": [], "void": []})
    r1 = optimize3d(spec)
    r2 = optimize3d(spec)
    assert r1.converged and r1.n_iter < 200
    h = r1.history["compliance"]
    assert all(h[i + 1] <= h[i] * 1.02 for i in range(len(h) - 1))
    assert abs(r1.rho.mean() - 0.4) < 0.004
    assert np.array_equal(r1.rho, r2.rho)


def test_preserve_void_moi_vong_3d(tmp_path):
    spec = mk(tmp_path, {
        "nelx": 12, "nely": 12, "nelz": 12, "volfrac": 0.35,
        "loads": [{"x": 12, "y": 6, "z": 6, "fy": -1.0}],
        "supports": [{"face": "x0", "dof": "all"}],
        "material": {"E": 1.0, "nu": 0.3},
        "simp": {"p": 3.0, "rmin": 1.3},
        "preserve": [{"type": "box", "x0": 0, "y0": 0, "z0": 0,
                      "x1": 0, "y1": 11, "z1": 11}],
        "void": [{"type": "sphere", "cx": 6.0, "cy": 3.0, "cz": 6.0,
                  "r": 2.0}]})
    grid = Grid3D(spec)
    violations = []

    def watchdog(i, rho, c):
        if not (rho[grid.preserve_mask] == 1.0).all():
            violations.append(("preserve", i))
        if not (rho[grid.void_mask] == 0.0).all():
            violations.append(("void", i))

    optimize3d(spec, max_iter=10, callback=watchdog)
    assert violations == []


# ── DoD-1.5: đối xứng gương theo z ─────────────────────────────

def test_dod_1_5_doi_xung_z(tmp_path):
    nz = 8
    loads = [{"x": 24, "y": 12, "z": z, "fy": -(0.5 if z in (0, nz) else 1.0)}
             for z in range(nz + 1)]
    spec = mk(tmp_path, {
        "nelx": 24, "nely": 12, "nelz": nz, "volfrac": 0.3,
        "loads": loads, "supports": [{"face": "x0", "dof": "all"}],
        "material": {"E": 1.0, "nu": 0.3},
        "simp": {"p": 3.0, "rmin": 1.5}, "preserve": [], "void": []})
    res = optimize3d(spec)
    assert res.converged
    mirrored = res.rho[:, :, ::-1]
    rel = np.linalg.norm(res.rho - mirrored) / np.linalg.norm(res.rho)
    assert rel < 0.01


# ── DoD-1.1: benchmark 60×20×4 vs reference monolithic ──────────

def reference_top3d_style(nelx, nely, nelz, volfrac, penal, rmin,
                          max_it=200):
    """Bản monolithic ĐỘC LẬP theo thuật toán công bố (Liu & Tovar 2014).

    Tự đánh số node, tự lắp ráp, tự filter (vòng for tường minh), tự OC.
    KE lấy từ quadrature bậc 3 — đường đã kiểm 2-đường ở tầng 1.2.
    Cùng bài toán với examples/spec3d_cantilever_60x20x4.json.
    """
    ke = _ke_quadrature(1.0, 0.3, 3)
    e0, e_min = 1.0, 1e-9
    nel = nelx * nely * nelz

    def nid(x, y, z):
        return z * (nelx + 1) * (nely + 1) + x * (nely + 1) + y

    edof = np.zeros((nel, 24), dtype=int)
    e = 0
    for ex in range(nelx):
        for ey in range(nely):
            for ez in range(nelz):
                ns = [nid(ex, ey, ez), nid(ex + 1, ey, ez),
                      nid(ex + 1, ey + 1, ez), nid(ex, ey + 1, ez),
                      nid(ex, ey, ez + 1), nid(ex + 1, ey, ez + 1),
                      nid(ex + 1, ey + 1, ez + 1), nid(ex, ey + 1, ez + 1)]
                edof[e] = [3 * n + d for n in ns for d in range(3)]
                e += 1
    n_dof = 3 * (nelx + 1) * (nely + 1) * (nelz + 1)
    i_k = np.repeat(edof, 24, axis=1).ravel()
    j_k = np.tile(edof, (1, 24)).ravel()
    force = np.zeros(n_dof)
    for z in range(nelz + 1):
        w = 0.125 if z in (0, nelz) else 0.25
        force[3 * nid(nelx, nely, z) + 1] = -w
    fixed = np.array(sorted({d for y in range(nely + 1)
                             for z in range(nelz + 1)
                             for d in (3 * nid(0, y, z), 3 * nid(0, y, z) + 1,
                                       3 * nid(0, y, z) + 2)}))
    free = np.setdiff1d(np.arange(n_dof), fixed)

    # filter H tường minh (thứ tự element của CHÍNH reference)
    reach = int(np.ceil(rmin)) - 1
    coords = np.array([(ex, ey, ez) for ex in range(nelx)
                       for ey in range(nely) for ez in range(nelz)])
    idx_of = {(ex, ey, ez): i for i, (ex, ey, ez) in enumerate(map(tuple, coords))}
    i_h, j_h, s_h = [], [], []
    for i, (ex, ey, ez) in enumerate(map(tuple, coords)):
        for dx in range(-reach, reach + 1):
            for dy in range(-reach, reach + 1):
                for dz in range(-reach, reach + 1):
                    nx2, ny2, nz2 = ex + dx, ey + dy, ez + dz
                    if 0 <= nx2 < nelx and 0 <= ny2 < nely and 0 <= nz2 < nelz:
                        w = rmin - np.sqrt(dx * dx + dy * dy + dz * dz)
                        if w > 0:
                            i_h.append(i)
                            j_h.append(idx_of[(nx2, ny2, nz2)])
                            s_h.append(w)
    h_mat = coo_matrix((s_h, (i_h, j_h)), shape=(nel, nel)).tocsr()
    h_sum = np.asarray(h_mat.sum(1)).flatten()

    x = np.full(nel, volfrac)
    change, loop, c = 1.0, 0, np.inf
    while change > 0.01 and loop < max_it:
        loop += 1
        xp = x ** penal
        s_k = ((ke.ravel()[None, :]) * (e_min + xp * (e0 - e_min))[:, None]).ravel()
        k_glob = coo_matrix((s_k, (i_k, j_k)), shape=(n_dof, n_dof)).tocsc()
        u = np.zeros(n_dof)
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


def test_dod_1_1_benchmark_top3d():
    """Cửa ải Stage 1: GP modular vs monolithic độc lập, cùng thuật toán."""
    res = optimize3d(load_spec3d(EXAMPLES / "spec3d_cantilever_60x20x4.json"))
    assert res.converged
    assert res.n_iter < 200
    c_ref, _ = reference_top3d_style(60, 20, 4, 0.3, 3.0, 1.5)
    assert abs(res.compliance - c_ref) / c_ref < 0.05
    # DoD-0.2 bản 3D: không checkerboard trên lát giữa
    b = (res.rho[:, :, 2] > 0.5).astype(int)
    cb = ((b[:-1, :-1] == b[1:, 1:]) & (b[1:, :-1] == b[:-1, 1:])
          & (b[:-1, :-1] != b[1:, :-1])).sum()
    assert int(cb) == 0
    assert abs(res.rho.mean() - 0.3) < 0.003
