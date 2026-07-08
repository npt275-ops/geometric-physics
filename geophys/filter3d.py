"""Sensitivity Filter 3D — kernel cầu bán kính rmin, chống checkerboard.

dcₙ(e) = Σⱼ wⱼ·ρⱼ·dcⱼ / (max(ρₑ,1e-3)·Σⱼ wⱼ),  w = max(0, rmin − dist3D).
Cài bằng scipy.ndimage.convolve (kernel 3D tiền tính, biên zero-pad).
Đối chứng bản O(N²) tường minh: tests/test_optimize3d.py.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import convolve


class SensitivityFilter3D:
    """Precompute kernel + tổng trọng số biên một lần, apply nhiều lần."""

    def __init__(self, nelx: int, nely: int, nelz: int, rmin: float) -> None:
        if rmin <= 0:
            raise ValueError(f"rmin phải > 0, nhận được {rmin}")
        self.shape = (nelx, nely, nelz)
        self.rmin = float(rmin)
        reach = int(np.ceil(rmin)) - 1
        offs = np.arange(-reach, reach + 1)
        dx, dy, dz = np.meshgrid(offs, offs, offs, indexing="ij")
        self.kernel = np.maximum(
            0.0, rmin - np.sqrt(dx ** 2 + dy ** 2 + dz ** 2))
        self.weight_sum = convolve(
            np.ones(self.shape), self.kernel, mode="constant", cval=0.0)

    def apply(self, rho: np.ndarray, dc: np.ndarray) -> np.ndarray:
        for name, arr in (("rho", rho), ("dc", dc)):
            if np.asarray(arr).shape != self.shape:
                raise ValueError(
                    f"{name} shape {np.asarray(arr).shape} — kỳ vọng {self.shape}")
        numerator = convolve(rho * dc, self.kernel,
                             mode="constant", cval=0.0)
        return numerator / (self.weight_sum * np.maximum(rho, 1e-3))
