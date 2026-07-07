"""OC Update — Optimality Criteria với bisection Lagrange multiplier.

xnewₑ = clip( ρₑ·√(−dcₑ/(dvₑ·λ)),  [ρₑ−move, ρₑ+move] ∩ [0, 1] )
preserve ép ρ = 1, void ép ρ = 0 TRƯỚC khi tính thể tích.
Bisection λ đến (λ2−λ1)/(λ1+λ2) < 1e-6, tối đa 200 vòng.

dc dương (nhiễu số sau filter) được kẹp về 0 trong căn — có chủ đích:
element có gradient "sai dấu" không được thưởng vật liệu.
"""

from __future__ import annotations

import numpy as np

_MAX_BISECT = 200
_TOL = 1e-6


def oc_update(rho: np.ndarray, dc: np.ndarray, dv: np.ndarray,
              volfrac: float, preserve_mask: np.ndarray,
              void_mask: np.ndarray, move: float = 0.2) -> np.ndarray:
    """Một bước cập nhật mật độ. Trả về xnew (nelx, nely) ∈ [0, 1].

    Raises:
        ValueError: shape lệch nhau, hoặc volume target bất khả thi
            với preserve/void đã cho.
        RuntimeError: bisection không hội tụ sau 200 vòng.
    """
    rho = np.asarray(rho, dtype=np.float64)
    shape = rho.shape
    for name, arr in (("dc", dc), ("dv", dv),
                      ("preserve_mask", preserve_mask),
                      ("void_mask", void_mask)):
        if np.asarray(arr).shape != shape:
            raise ValueError(
                f"{name} shape {np.asarray(arr).shape} — kỳ vọng {shape}")

    nel = rho.size
    target = volfrac * nel
    n_preserve = int(preserve_mask.sum())
    n_void = int(void_mask.sum())
    if target < n_preserve or target > nel - n_void:
        raise ValueError(
            f"volume target {target:.1f} bất khả thi: preserve chiếm "
            f"{n_preserve}, khả dụng tối đa {nel - n_void} / {nel} element")

    neg_dc = np.maximum(-np.asarray(dc, dtype=np.float64), 0.0)
    dv = np.asarray(dv, dtype=np.float64)

    l1, l2 = 0.0, 1e9
    for _ in range(_MAX_BISECT):
        lmid = 0.5 * (l1 + l2)
        be = np.sqrt(neg_dc / (dv * lmid))
        xnew = np.clip(rho * be, rho - move, rho + move)
        xnew = np.clip(xnew, 0.0, 1.0)
        xnew[preserve_mask] = 1.0
        xnew[void_mask] = 0.0
        if xnew.sum() > target:
            l1 = lmid
        else:
            l2 = lmid
        if (l2 - l1) / (l1 + l2) < _TOL:
            return xnew
    raise RuntimeError(
        f"OC bisection không hội tụ sau {_MAX_BISECT} vòng "
        f"(λ ∈ [{l1:.3e}, {l2:.3e}]) — kiểm tra dc/dv đầu vào")
