"""Acceptance Tầng 0.5 — render2d (spec stage0-t5 mục 8)."""

import importlib
import json
import subprocess
import sys

import numpy as np
import pytest
from PIL import Image

from geophys.render2d import FrameRecorder, render_field


# ── PNG ─────────────────────────────────────────────────────────

def test_png_kich_thuoc_va_ngu_nghia_pixel(tmp_path):
    rho = np.full((6, 4), 0.5)
    rho[0, 0] = 1.0   # element góc trên-trái → pixel ĐEN góc trên-trái
    rho[5, 3] = 0.0   # element góc dưới-phải → TRẮNG
    out = render_field(rho, tmp_path / "f.png", scale=8)
    img = Image.open(out)
    assert img.size == (6 * 8, 4 * 8)  # (width=nelx·s, height=nely·s)
    assert img.getpixel((0, 0)) < 10          # đặc = đen
    assert img.getpixel((47, 31)) > 245       # rỗng = trắng
    assert 100 < img.getpixel((24, 16)) < 155  # 0.5 = xám giữa


def test_rho_ngoai_khoang_raise(tmp_path):
    with pytest.raises(ValueError):
        render_field(np.full((3, 3), 1.2), tmp_path / "x.png")
    with pytest.raises(ValueError):
        render_field(np.ones((3, 3, 3)), tmp_path / "x.png")


# ── GIF qua callback optimize ───────────────────────────────────

def test_gif_tu_optimize_that(tmp_path):
    from geophys.optimize import optimize
    from geophys.spec_loader import load_spec
    data = {"nelx": 12, "nely": 8, "volfrac": 0.4,
            "loads": [{"x": 12, "y": 4, "fx": 0.0, "fy": -1.0}],
            "supports": [{"edge": "left", "dof": "both"}],
            "material": {"E": 1.0, "nu": 0.3},
            "simp": {"p": 3.0, "rmin": 1.3},
            "preserve": [], "void": []}
    f = tmp_path / "s.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    rec = FrameRecorder(every=2, scale=4)
    res = optimize(load_spec(f), callback=rec)
    gif = rec.save_gif(tmp_path / "evo.gif", fps=10)
    img = Image.open(gif)
    assert img.is_animated
    assert img.n_frames == res.n_iter // 2
    assert img.size == (12 * 4, 8 * 4)


def test_save_gif_khong_khung_raise(tmp_path):
    with pytest.raises(ValueError):
        FrameRecorder().save_gif(tmp_path / "x.gif")


def test_every_khong_hop_le():
    with pytest.raises(ValueError):
        FrameRecorder(every=0)


# ── Headless guard: engine không kéo matplotlib/PIL ─────────────

def test_engine_khong_import_thu_vien_render():
    """Import TOÀN BỘ engine trong process sạch → không có matplotlib/PIL."""
    code = (
        "import sys\n"
        "import geophys, geophys.spec_loader, geophys.grid2d, "
        "geophys.fea2d, geophys.sensitivity, geophys.filter2d, "
        "geophys.oc_update, geophys.optimize\n"
        "bad = [m for m in ('matplotlib', 'PIL') if m in sys.modules]\n"
        "assert not bad, f'engine keo theo {bad}'\n"
        "import geophys.render2d\n"
        "assert 'PIL' in sys.modules\n"
        "print('HEADLESS-OK')\n"
    )
    result = subprocess.run([sys.executable, "-c", code],
                            capture_output=True, text=True, check=False)
    assert "HEADLESS-OK" in result.stdout, result.stderr
