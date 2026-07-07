"""Loader cho spec.json schema v0 (bài toán 2D).

Problem-as-Data: bài toán là dữ liệu, không phải thao tác giao diện.
Mọi lỗi → SpecError(field, reason, hint) — nêu ĐÚNG TÊN TRƯỜNG.

Quy ước lưới (thứ tự top88 để so nghiệm chuẩn):
- Node đánh số cột-trước: node_id = x * (nely + 1) + y, với x ∈ [0, nelx],
  y ∈ [0, nely], gốc tọa độ góc trên-trái, y hướng xuống.
- Element đánh số cột-trước: element_id = ex * nely + ey.
- Vùng (Region) là hình chữ nhật theo tọa độ ELEMENT, biên bao gồm.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from geophys.errors import SpecError

VALID_EDGES = ("left", "right", "top", "bottom")
VALID_DOFS = ("x", "y", "both")

_REQUIRED_FIELDS = (
    "nelx", "nely", "volfrac", "loads", "supports",
    "material", "simp", "preserve", "void",
)


@dataclass(frozen=True)
class Region:
    """Hình chữ nhật theo tọa độ element, biên bao gồm [x0..x1] × [y0..y1]."""

    x0: int
    y0: int
    x1: int
    y1: int

    def overlaps(self, other: "Region") -> bool:
        return not (
            self.x1 < other.x0 or other.x1 < self.x0
            or self.y1 < other.y0 or other.y1 < self.y0
        )


@dataclass(frozen=True)
class Load:
    node: int
    fx: float
    fy: float


@dataclass(frozen=True)
class Support:
    node: int
    dof: str  # "x" | "y" | "both"


@dataclass(frozen=True)
class Spec:
    nelx: int
    nely: int
    volfrac: float
    loads: tuple
    supports: tuple
    E: float
    nu: float
    p: float
    rmin: float
    preserve: tuple
    void: tuple


def _require_int(obj: dict, field: str, minimum: int) -> int:
    value = obj.get(field)
    if not isinstance(value, int) or isinstance(value, bool):
        raise SpecError(field, f"phải là số nguyên, nhận được {value!r}",
                        f"ví dụ: \"{field}\": 60")
    if value < minimum:
        raise SpecError(field, f"phải ≥ {minimum}, nhận được {value}",
                        "kích thước lưới phải dương")
    return value


def _require_number(obj: dict, field: str, lo: float, hi: float,
                    lo_open: bool = True, hi_open: bool = True) -> float:
    value = obj.get(field)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise SpecError(field, f"phải là số, nhận được {value!r}", "")
    value = float(value)
    lo_bad = value <= lo if lo_open else value < lo
    hi_bad = value >= hi if hi_open else value > hi
    if lo_bad or hi_bad:
        lo_b = "(" if lo_open else "["
        hi_b = ")" if hi_open else "]"
        raise SpecError(field,
                        f"phải nằm trong khoảng {lo_b}{lo}, {hi}{hi_b}, "
                        f"nhận được {value}", "")
    return value


def _node_id(x: int, y: int, nelx: int, nely: int, field: str) -> int:
    if not (0 <= x <= nelx) or not (0 <= y <= nely):
        raise SpecError(field,
                        f"tọa độ node ({x}, {y}) ngoài lưới "
                        f"[0..{nelx}] × [0..{nely}]",
                        "node tính theo lưới NODE, không phải element")
    return x * (nely + 1) + y


def _resolve_node(entry: dict, nelx: int, nely: int, field: str) -> int:
    if "node" in entry:
        node = entry["node"]
        n_nodes = (nelx + 1) * (nely + 1)
        if not isinstance(node, int) or isinstance(node, bool) \
                or not (0 <= node < n_nodes):
            raise SpecError(field,
                            f"node phải là int trong [0, {n_nodes - 1}], "
                            f"nhận được {node!r}", "")
        return node
    if "x" in entry and "y" in entry:
        return _node_id(entry["x"], entry["y"], nelx, nely, field)
    raise SpecError(field, "mỗi mục phải có 'node' hoặc cặp 'x','y'",
                    "ví dụ: {\"x\": 0, \"y\": 0, ...}")


def _edge_nodes(edge: str, nelx: int, nely: int, field: str) -> list:
    if edge not in VALID_EDGES:
        raise SpecError(field, f"edge phải thuộc {VALID_EDGES}, "
                        f"nhận được {edge!r}", "")
    if edge == "left":
        return [_node_id(0, y, nelx, nely, field) for y in range(nely + 1)]
    if edge == "right":
        return [_node_id(nelx, y, nelx, nely, field) for y in range(nely + 1)]
    if edge == "top":
        return [_node_id(x, 0, nelx, nely, field) for x in range(nelx + 1)]
    return [_node_id(x, nely, nelx, nely, field) for x in range(nelx + 1)]


def _parse_loads(raw, nelx: int, nely: int) -> tuple:
    if not isinstance(raw, list) or not raw:
        raise SpecError("loads", "phải là list không rỗng",
                        "ít nhất một lực đặt lên lưới")
    loads = []
    for i, entry in enumerate(raw):
        field = f"loads[{i}]"
        if not isinstance(entry, dict):
            raise SpecError(field, "mỗi mục phải là object", "")
        node = _resolve_node(entry, nelx, nely, field)
        fx = entry.get("fx", 0.0)
        fy = entry.get("fy", 0.0)
        for name, val in (("fx", fx), ("fy", fy)):
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise SpecError(f"{field}.{name}",
                                f"phải là số, nhận được {val!r}", "")
        if fx == 0.0 and fy == 0.0:
            raise SpecError(field, "lực bằng 0 (fx = fy = 0)",
                            "khai ít nhất một thành phần khác 0")
        loads.append(Load(node=node, fx=float(fx), fy=float(fy)))
    return tuple(loads)


def _parse_supports(raw, nelx: int, nely: int) -> tuple:
    if not isinstance(raw, list) or not raw:
        raise SpecError("supports", "phải là list không rỗng",
                        "không có ngàm thì bài toán không giải được (rigid body)")
    supports = []
    for i, entry in enumerate(raw):
        field = f"supports[{i}]"
        if not isinstance(entry, dict):
            raise SpecError(field, "mỗi mục phải là object", "")
        dof = entry.get("dof", "both")
        if dof not in VALID_DOFS:
            raise SpecError(f"{field}.dof",
                            f"phải thuộc {VALID_DOFS}, nhận được {dof!r}", "")
        if "edge" in entry:
            nodes = _edge_nodes(entry["edge"], nelx, nely, field)
        else:
            nodes = [_resolve_node(entry, nelx, nely, field)]
        supports.extend(Support(node=n, dof=dof) for n in nodes)
    return tuple(supports)


def _parse_regions(raw, name: str, nelx: int, nely: int) -> tuple:
    if not isinstance(raw, list):
        raise SpecError(name, "phải là list (được phép rỗng)", "")
    regions = []
    for i, entry in enumerate(raw):
        field = f"{name}[{i}]"
        if not isinstance(entry, dict):
            raise SpecError(field, "mỗi vùng phải là object x0/y0/x1/y1", "")
        try:
            r = Region(x0=int(entry["x0"]), y0=int(entry["y0"]),
                       x1=int(entry["x1"]), y1=int(entry["y1"]))
        except KeyError as exc:
            raise SpecError(field, f"thiếu trường {exc.args[0]!r}",
                            "vùng cần đủ x0, y0, x1, y1") from exc
        if r.x0 > r.x1 or r.y0 > r.y1:
            raise SpecError(field, f"x0 ≤ x1 và y0 ≤ y1 bắt buộc, nhận {r}", "")
        if not (0 <= r.x0 and r.x1 < nelx and 0 <= r.y0 and r.y1 < nely):
            raise SpecError(field,
                            f"vùng {r} ngoài lưới element "
                            f"[0..{nelx - 1}] × [0..{nely - 1}]",
                            "vùng tính theo lưới ELEMENT, không phải node")
        regions.append(r)
    return tuple(regions)


def load_spec(path) -> Spec:
    """Đọc + validate spec.json schema v0. Trả về Spec bất biến."""
    p = Path(path)
    if not p.is_file():
        raise SpecError("file", "không tìm thấy file spec",
                        f"đường dẫn đã thử: {p.resolve()}")
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SpecError("json", f"JSON hỏng tại dòng {exc.lineno}, "
                        f"cột {exc.colno}: {exc.msg}",
                        "kiểm tra dấu phẩy / ngoặc") from exc
    if not isinstance(raw, dict):
        raise SpecError("json", "spec phải là JSON object", "")

    for name in _REQUIRED_FIELDS:
        if name not in raw:
            raise SpecError(name, "trường bắt buộc bị thiếu",
                            f"khai \"{name}\" trong spec.json")

    nelx = _require_int(raw, "nelx", 1)
    nely = _require_int(raw, "nely", 1)
    volfrac = _require_number(raw, "volfrac", 0.0, 1.0)

    material = raw["material"]
    if not isinstance(material, dict):
        raise SpecError("material", "phải là object {E, nu}", "")
    e_mod = _require_number(material, "E", 0.0, float("inf"))
    nu = _require_number(material, "nu", 0.0, 0.5)

    simp = raw["simp"]
    if not isinstance(simp, dict):
        raise SpecError("simp", "phải là object {p, rmin}", "")
    if "p" not in simp:
        simp = {**simp, "p": 3.0}
    p_pen = _require_number(simp, "p", 0.0, float("inf"))
    rmin = _require_number(simp, "rmin", 0.0, float("inf"))

    loads = _parse_loads(raw["loads"], nelx, nely)
    supports = _parse_supports(raw["supports"], nelx, nely)
    preserve = _parse_regions(raw["preserve"], "preserve", nelx, nely)
    void = _parse_regions(raw["void"], "void", nelx, nely)

    for i, pr in enumerate(preserve):
        for j, vr in enumerate(void):
            if pr.overlaps(vr):
                raise SpecError(f"preserve[{i}]/void[{j}]",
                                f"vùng bảo tồn {pr} giao vùng cấm {vr}",
                                "hai loại vùng phải rời nhau")

    return Spec(nelx=nelx, nely=nely, volfrac=volfrac, loads=loads,
                supports=supports, E=e_mod, nu=nu, p=p_pen, rmin=rmin,
                preserve=preserve, void=void)
