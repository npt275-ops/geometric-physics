"""Generator spec bàn đạp phanh — deterministic, sinh 4 file examples/.

Hình học theo specs/stage2-t3-brake-pedal.md (NGƯỜI duyệt qua ảnh render):
- Không gian 160×80×20mm; pivot trụ preserve r=12mm + lỗ void r=6mm tại
  (20mm, 40mm) xuyên z; ngàm vành node quanh lỗ; pad preserve 16×8×20mm
  góc trên-phải; 3 load case (1200N / lệch 15° / 360N ngang).
- Bản full: 80×40×10 voxel h=2mm. Bản smoke: 40×20×5 voxel h=4mm.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "examples"

F_MAIN = 1200.0
ANGLE_DEG = 15.0
F_SIDE = 0.3 * F_MAIN


def _pad_loads(nelx, nely, nelz, pad_x0, fx, fy, fz):
    """Phân bố lực trên node mặt y=0 vùng pad, trọng số biên 0.5/góc 0.25."""
    xs = list(range(pad_x0, nelx + 1))
    zs = list(range(0, nelz + 1))
    weights = {}
    for x in xs:
        for z in zs:
            w = ((0.5 if x in (xs[0], xs[-1]) else 1.0)
                 * (0.5 if z in (zs[0], zs[-1]) else 1.0))
            weights[(x, z)] = w
    total_w = sum(weights.values())
    loads = []
    for (x, z), w in sorted(weights.items()):
        s = w / total_w
        entry = {"x": x, "y": 0, "z": z}
        if fx:
            entry["fx"] = round(fx * s, 6)
        if fy:
            entry["fy"] = round(fy * s, 6)
        if fz:
            entry["fz"] = round(fz * s, 6)
        loads.append(entry)
    return loads


def _pivot_supports(nelx, nely, nelz, cx, cy, r_node):
    """Ngàm vành node quanh lỗ trục (mô phỏng trục cứng), mọi lớp z."""
    sup = []
    for x in range(nelx + 1):
        for y in range(nely + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r_node ** 2:
                for z in range(nelz + 1):
                    sup.append({"x": x, "y": y, "z": z, "dof": "all"})
    return sup


def _pivot_ring_boxes(cx, cy, a, b, nelz):
    """Vành preserve quanh lỗ = 4 box (outer half-width a, inner b) —
    né overlap với void (luật preserve∩void=∅ của Grid3D)."""
    z0, z1 = 0, nelz - 1
    return [
        {"type": "box", "x0": cx - a, "y0": cy - a, "z0": z0,
         "x1": cx + a, "y1": cy - b - 1, "z1": z1},          # trên
        {"type": "box", "x0": cx - a, "y0": cy + b + 1, "z0": z0,
         "x1": cx + a, "y1": cy + a, "z1": z1},              # dưới
        {"type": "box", "x0": cx - a, "y0": cy - b, "z0": z0,
         "x1": cx - b - 1, "y1": cy + b, "z1": z1},          # trái
        {"type": "box", "x0": cx + b + 1, "y0": cy - b, "z0": z0,
         "x1": cx + a, "y1": cy + b, "z1": z1},              # phải
    ]


def build(nelx, nely, nelz, h_mm, rmin, cx, cy, r_pre, r_hole, r_node,
          pad_x0, pad_y1, ring_inner):
    ang = math.radians(ANGLE_DEG)
    case1 = _pad_loads(nelx, nely, nelz, pad_x0, 0.0, F_MAIN, 0.0)
    case2 = _pad_loads(nelx, nely, nelz, pad_x0,
                       -F_MAIN * math.sin(ang), F_MAIN * math.cos(ang), 0.0)
    case3 = _pad_loads(nelx, nely, nelz, pad_x0, 0.0, 0.0, F_SIDE)
    common = {
        "nelx": nelx, "nely": nely, "nelz": nelz,
        "volfrac": 0.45,
        "element_size_mm": h_mm,
        "material_name": "nhom_6061_t6",
        "supports": _pivot_supports(nelx, nely, nelz, cx, cy, r_node),
        "simp": {"p": 3.0, "rmin": rmin},
        "preserve": _pivot_ring_boxes(cx, cy, int(r_pre), ring_inner,
                                      nelz) + [
            {"type": "box", "x0": pad_x0, "y0": 0, "z0": 0,
             "x1": nelx - 1, "y1": pad_y1, "z1": nelz - 1},
        ],
        "void": [
            {"type": "cylinder", "axis": "z", "cx": float(cx),
             "cy": float(cy), "r": float(r_hole), "z0": 0, "z1": nelz - 1},
        ],
    }
    multi = dict(common)
    multi["_comment"] = ("Ban dap phanh nhom 6061 — 3 load case "
                         "(1200N / lech 15 do / 360N ngang). "
                         "Sinh boi gen_brake_pedal_spec.py — DUNG sua tay.")
    multi["load_cases"] = [
        {"weight": 1.0, "loads": case1},
        {"weight": 0.5, "loads": case2},
        {"weight": 0.3, "loads": case3},
    ]
    single = dict(common)
    single["_comment"] = ("Ban doi chung DoD-2.1: CHI case chinh 1200N. "
                          "Sinh boi gen_brake_pedal_spec.py.")
    single["loads"] = case1
    return multi, single


def main() -> None:
    OUT.mkdir(exist_ok=True)
    # Bản FULL: 80×40×10, h=2mm — pivot (10,20) elem, r 6/3 elem = 12/6mm
    full_m, full_s = build(80, 40, 10, 2.0, 2.5,
                           cx=10, cy=20, r_pre=6.0, r_hole=3.0, r_node=3.4,
                           pad_x0=72, pad_y1=3, ring_inner=3)
    # Bản SMOKE: 40×20×5, h=4mm — cùng kích thước vật lý
    smoke_m, smoke_s = build(40, 20, 5, 4.0, 2.0,
                             cx=5, cy=10, r_pre=3.0, r_hole=1.5, r_node=1.8,
                             pad_x0=36, pad_y1=1, ring_inner=2)
    for name, data in (("spec_brake_pedal.json", full_m),
                       ("spec_brake_pedal_single.json", full_s),
                       ("spec_brake_smoke.json", smoke_m),
                       ("spec_brake_smoke_single.json", smoke_s)):
        (OUT / name).write_text(
            json.dumps(data, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8")
        print("sinh", name)


if __name__ == "__main__":
    main()
