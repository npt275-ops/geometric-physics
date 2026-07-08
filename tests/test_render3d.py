"""Acceptance Tầng 1.6 — render 3D + HTML viewer (spec stage1-t6 mục 8)."""

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from geophys.optimize3d import optimize3d
from geophys.render3d import SnapshotRecorder3D, render_isosurface
from geophys.spec3d import load_spec3d

SMALL = {"nelx": 10, "nely": 5, "nelz": 4, "volfrac": 0.4,
         "loads": [{"x": 10, "y": 5, "z": 2, "fy": -1.0}],
         "supports": [{"face": "x0", "dof": "all"}],
         "material": {"E": 1.0, "nu": 0.3},
         "simp": {"p": 3.0, "rmin": 1.3}, "preserve": [], "void": []}


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("r3d")
    f = tmp / "s.json"
    f.write_text(json.dumps(SMALL), encoding="utf-8")
    spec = load_spec3d(f)
    rec = SnapshotRecorder3D(every=3)
    res = optimize3d(spec, callback=rec)
    rec.add_final(res.n_iter, res.rho, res.compliance)
    return res, rec


def test_png_iso(tmp_path, run):
    res, _ = run
    out = render_isosurface(res.rho, tmp_path / "iso.png")
    img = Image.open(out)
    assert img.size[0] > 300 and out.stat().st_size > 10_000


def test_recorder_dung_moc(run):
    res, rec = run
    iters = [n for n, _, _ in rec.snapshots]
    assert iters[0] == 3 and iters[-1] == res.n_iter
    assert all(b - a in (3, 1, 2) for a, b in zip(iters, iters[1:]))
    assert len(iters) >= 5


def test_html_tu_chua_va_du_khung(tmp_path, run):
    _, rec = run
    out = rec.to_html(tmp_path / "v.html")
    html = out.read_text(encoding="utf-8")
    # offline tuyệt đối — không tài nguyên ngoài
    assert "http://" not in html and "https://" not in html
    assert "<canvas" in html and 'type="range"' in html
    assert '"wheel"' in html and '"mousedown"' in html
    # đủ khung: FRAMES là mảng N phần tử có trường v/f
    n_meshes = html.count('"scale"')
    assert n_meshes == len(rec.snapshots)
    assert out.stat().st_size > 50_000  # có dữ liệu mesh thật


def test_html_khong_snapshot_raise(tmp_path):
    with pytest.raises(ValueError):
        SnapshotRecorder3D(every=2).to_html(tmp_path / "x.html")
    with pytest.raises(ValueError):
        SnapshotRecorder3D(every=0)


def test_render_pngs_theo_moc(tmp_path, run):
    _, rec = run
    paths = rec.render_pngs(tmp_path)
    assert len(paths) == len(rec.snapshots)
    assert all(p.is_file() for p in paths)
