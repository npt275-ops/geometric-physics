"""Sensitivity Filter — bán kính rmin, chống checkerboard (module BẮT BUỘC).

Kiểu top88:  dcₙ(e) = Σⱼ wⱼ·ρⱼ·dcⱼ / (max(ρₑ, 1e-3)·Σⱼ wⱼ),
             wⱼ = max(0, rmin − dist(e, j)).

Trên lưới đều, trọng số chỉ phụ thuộc khoảng cách → cài bằng convolution
với kernel cố định. Không vòng for Python trên element.
Đối chứng độc lập với bản O(N²) tường minh: tests/test_filter2d.py.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import convolve2d


class SensitivityFilter:
    """Precompute kernel + tổng trọng số biên một lần, apply nhiều lần."""

    def __init__(self, nelx: int, nely: int, rmin: float) -> None:
        if rmin <= 0:
            raise ValueError(f"rmin phải > 0, nhận được {rmin}")
        self.nelx = nelx
        self.nely = nely
        self.rmin = float(rmin)

        reach = int(np.ceil(rmin)) - 1
        offsets = np.arange(-reach, reach + 1)
        dx, dy = np.meshgrid(offsets, offsets, indexing="ij")
        kernel = np.maximum(0.0, rmin - np.sqrt(dx ** 2 + dy ** 2))
        self.kernel = kernel
        # Σⱼ wⱼ từng vị trí (biên nhỏ hơn tâm) — convolve trường 1
        self.weight_sum = convolve2d(
            np.ones((nelx, nely)), kernel, mode="same", boundary="fill")

    def apply(self, rho: np.ndarray, dc: np.ndarray) -> np.ndarray:
        """Lọc trường sensitivity. Trả về cùng shape (nelx, nely)."""
        expected = (self.nelx, self.nely)
        for name, arr in (("rho", rho), ("dc", dc)):
            if np.asarray(arr).shape != expected:
                raise ValueError(
                    f"{name} shape {np.asarray(arr).shape} — kỳ vọng {expected}")
        numerator = convolve2d(
            rho * dc, self.kernel, mode="same", boundary="fill")
        return numerator / (self.weight_sum * np.maximum(rho, 1e-3))
