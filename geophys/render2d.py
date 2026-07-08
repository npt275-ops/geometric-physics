"""Render Module 2D — PNG trường mật độ + GIF "ăn mòn" (DoD-0.8).

Lớp TÁCH RỜI khỏi engine: chỉ đọc rho, nối với optimize qua callback.
Engine không import module này; module này không import engine.
Quy ước hiển thị: đặc (ρ=1) = ĐEN, rỗng (ρ=0) = TRẮNG, y hướng xuống.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


def _to_image(rho: np.ndarray, scale: int) -> Image.Image:
    rho = np.asarray(rho, dtype=np.float64)
    if rho.ndim != 2:
        raise ValueError(f"rho phải 2 chiều, nhận được ndim={rho.ndim}")
    if rho.min() < 0.0 or rho.max() > 1.0:
        raise ValueError(
            f"rho ngoài [0,1]: min={rho.min():.3g}, max={rho.max():.3g}")
    # (nelx, nely) → ảnh (rows=nely, cols=nelx), y hướng xuống → transpose
    gray = np.round((1.0 - rho.T) * 255.0).astype(np.uint8)
    img = Image.fromarray(gray, mode="L")
    if scale != 1:
        img = img.resize((rho.shape[0] * scale, rho.shape[1] * scale),
                         resample=Image.NEAREST)
    return img


def render_field(rho: np.ndarray, path, scale: int = 8) -> Path:
    """Xuất một khung PNG. Trả về Path đã ghi."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    _to_image(rho, scale).save(out, format="PNG")
    return out


class FrameRecorder:
    """Callback cho optimize(): chụp khung mỗi `every` vòng, ghép GIF.

    Dùng:  rec = FrameRecorder(every=1)
           optimize(spec, callback=rec)
           rec.save_gif("evolution.gif")
    """

    def __init__(self, every: int = 1, scale: int = 8) -> None:
        if every < 1:
            raise ValueError(f"every phải ≥ 1, nhận được {every}")
        self.every = every
        self.scale = scale
        self.frames: list = []
        self.compliances: list = []

    def __call__(self, n_iter: int, rho: np.ndarray, c: float) -> None:
        if n_iter % self.every == 0:
            self.frames.append(_to_image(rho, self.scale))
            self.compliances.append(float(c))

    def save_gif(self, path, fps: int = 10) -> Path:
        """Ghép GIF lặp vô hạn, khung cuối giữ 1 giây."""
        if not self.frames:
            raise ValueError(
                "Chưa có khung nào — FrameRecorder phải được truyền vào "
                "optimize(callback=...) trước khi save_gif")
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        duration = [max(1000 // fps, 20)] * len(self.frames)
        duration[-1] = 1000  # dừng ở kết quả cuối 1s
        self.frames[0].save(
            out, format="GIF", save_all=True,
            append_images=self.frames[1:], duration=duration, loop=0)
        return out
