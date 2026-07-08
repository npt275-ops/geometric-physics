"""Export Module — trường mật độ 3D → STL kín (watertight).

Pipeline: pad biên 0 (chống mesh hở — đối sách S1-R3) → marching cubes
(isosurface) → lọc mảnh vụn <1% (minh bạch qua report) → Taubin smoothing
(λ=0.5, ν=0.53 — co/nở xen kẽ giữ thể tích) → kiểm trimesh → STL binary + report.

Một chiều tuyệt đối: module này ĐỌC rho, engine không biết nó tồn tại.
Không bao giờ trả file rác: mesh hỏng → ExportError kèm số liệu.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import trimesh
from skimage.measure import marching_cubes
from trimesh.smoothing import filter_taubin


class ExportError(Exception):
    """Mesh sau pipeline không đạt chuẩn xuất xưởng (watertight/kích thước)."""


def rho_to_mesh(rho: np.ndarray, iso: float = 0.5,
                smooth_iters: int = 10) -> tuple:
    """rho → (trimesh.Trimesh, report dict). Chưa ghi file."""
    rho = np.asarray(rho, dtype=np.float64)
    if rho.ndim != 3:
        raise ValueError(f"rho phải 3 chiều, nhận ndim={rho.ndim}")
    if not (0.0 < iso < 1.0):
        raise ValueError(f"iso phải trong (0,1), nhận {iso}")
    n_solid = int((rho > iso).sum())
    if n_solid == 0:
        raise ValueError(
            f"Không có vật chất trên isosurface {iso} — rho.max()={rho.max():.3g}")

    padded = np.pad(rho, 1, mode="constant", constant_values=0.0)
    verts, faces, _, _ = marching_cubes(padded, level=iso)
    verts -= 1.0  # bù lớp pad — tọa độ khớp lưới voxel gốc
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)

    # Lọc mảnh vụn < 1% tổng thể tích — ghi report, không lặng lẽ
    parts = mesh.split(only_watertight=False)
    n_raw = len(parts)
    if n_raw > 1:
        vols = np.array([abs(p.volume) for p in parts])
        keep = [p for p, v in zip(parts, vols) if v >= 0.01 * vols.sum()]
        mesh = trimesh.util.concatenate(keep) if len(keep) > 1 else keep[0]
    n_kept = len(mesh.split(only_watertight=False))

    if smooth_iters > 0:
        filter_taubin(mesh, lamb=0.5, nu=0.53, iterations=smooth_iters)

    report = {
        "watertight": bool(mesh.is_watertight),
        "n_components_raw": n_raw,
        "n_components": n_kept,
        "volume_stl": float(abs(mesh.volume)),
        "volume_voxel": float(n_solid),
        "volume_lech_pct": float(
            abs(abs(mesh.volume) - n_solid) / n_solid * 100),
        "n_faces": int(len(mesh.faces)),
        "iso": float(iso),
        "smooth_iters": int(smooth_iters),
    }
    return mesh, report


def export_stl(rho: np.ndarray, path, iso: float = 0.5,
               smooth_iters: int = 10) -> tuple:
    """rho → file STL binary + report. Mesh không watertight → ExportError."""
    mesh, report = rho_to_mesh(rho, iso=iso, smooth_iters=smooth_iters)
    if not report["watertight"]:
        raise ExportError(
            f"Mesh KHÔNG watertight (components={report['n_components']}, "
            f"faces={report['n_faces']}) — không xuất file rác. "
            "Thử tăng smooth_iters hoặc kiểm tra rho có mảnh rời.")
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(out, file_type="stl")
    report["path"] = str(out)
    report["size_kb"] = round(out.stat().st_size / 1024, 1)
    return out, report
