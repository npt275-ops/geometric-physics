"""Loader spec.json schema v1 — bài toán 3D voxel.

Khác v0: thêm nelz, lực 3 thành phần, support theo MẶT, vùng bảo tồn/cấm
bằng hình khối nguyên thủy (box/sphere/cylinder) thay vì liệt kê voxel.
Tái dùng validator của spec_loader (STABLE — chỉ GỌI, không sửa).

Quy ước (LOCK — xem specs/stage1-t1-spec-v1-grid3d.md):
node_id(x,y,z) = z·(nelx+1)(nely+1) + x·(nely+1) + y (lát z=0 trùng 2D).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from geophys.errors import SpecError
from geophys.spec_loader import _require_int, _require_number

VALID_FACES = ("x0", "x1", "y0", "y1", "z0", "z1")
VALID_DOFS3 = ("x", "y", "z", "all")
VALID_PRIMITIVES = ("box", "sphere", "cylinder")
VALID_AXES = ("x", "y", "z")

_REQUIRED = ("nelx", "nely", "nelz", "volfrac", "loads", "supports",
             "material", "simp", "preserve", "void")


@dataclass(frozen=True)
class Load3D:
    node: int
    fx: float
    fy: float
    fz: float


@dataclass(frozen=True)
class Support3D:
    node: int
    dof: str  # "x" | "y" | "z" | "all"


@dataclass(frozen=True)
class Primitive:
    """Hình khối nguyên thủy — giữ dạng dữ liệu thô đã validate.

    kind="box": params=(x0,y0,z0,x1,y1,z1) — tọa độ element, biên bao gồm.
    kind="sphere": params=(cx,cy,cz,r).
    kind="cylinder": params=(axis, c1,c2, r, a0,a1) — c1,c2 là 2 tọa độ tâm
        vuông góc trục theo thứ tự (x trước y trước z, bỏ trục); a0,a1 là
        khoảng dọc trục (element, biên bao gồm).
    """
    kind: str
    params: tuple


@dataclass(frozen=True)
class Spec3D:
    nelx: int
    nely: int
    nelz: int
    volfrac: float
    loads: tuple
    supports: tuple
    E: float
    nu: float
    p: float
    rmin: float
    preserve: tuple
    void: tuple


def _node_id3(x: int, y: int, z: int, nx: int, ny: int, nz: int,
              field: str) -> int:
    if not (0 <= x <= nx and 0 <= y <= ny and 0 <= z <= nz):
        raise SpecError(field,
                        f"tọa độ node ({x},{y},{z}) ngoài lưới "
                        f"[0..{nx}]×[0..{ny}]×[0..{nz}]",
                        "node theo lưới NODE, không phải element")
    return z * (nx + 1) * (ny + 1) + x * (ny + 1) + y


def _resolve_node3(entry: dict, nx: int, ny: int, nz: int,
                   field: str) -> int:
    if "node" in entry:
        node = entry["node"]
        n_nodes = (nx + 1) * (ny + 1) * (nz + 1)
        if not isinstance(node, int) or isinstance(node, bool) \
                or not (0 <= node < n_nodes):
            raise SpecError(field,
                            f"node phải là int trong [0, {n_nodes - 1}], "
                            f"nhận được {node!r}", "")
        return node
    if all(k in entry for k in ("x", "y", "z")):
        return _node_id3(entry["x"], entry["y"], entry["z"],
                         nx, ny, nz, field)
    raise SpecError(field, "mỗi mục cần 'node' hoặc đủ bộ 'x','y','z'", "")


def _face_nodes(face: str, nx: int, ny: int, nz: int, field: str) -> list:
    if face not in VALID_FACES:
        raise SpecError(field,
                        f"face phải thuộc {VALID_FACES}, nhận {face!r}", "")
    axis, side = face[0], face[1]
    fixed_val = {"x": nx, "y": ny, "z": nz}[axis] if side == "1" else 0
    nodes = []
    ranges = {"x": range(nx + 1), "y": range(ny + 1), "z": range(nz + 1)}
    ranges[axis] = (fixed_val,)
    for z in ranges["z"]:
        for x in ranges["x"]:
            for y in ranges["y"]:
                nodes.append(_node_id3(x, y, z, nx, ny, nz, field))
    return nodes


def _parse_loads3(raw, nx, ny, nz) -> tuple:
    if not isinstance(raw, list) or not raw:
        raise SpecError("loads", "phải là list không rỗng", "")
    out = []
    for i, entry in enumerate(raw):
        field = f"loads[{i}]"
        if not isinstance(entry, dict):
            raise SpecError(field, "mỗi mục phải là object", "")
        node = _resolve_node3(entry, nx, ny, nz, field)
        comps = {}
        for name in ("fx", "fy", "fz"):
            val = entry.get(name, 0.0)
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise SpecError(f"{field}.{name}",
                                f"phải là số, nhận {val!r}", "")
            comps[name] = float(val)
        if comps["fx"] == comps["fy"] == comps["fz"] == 0.0:
            raise SpecError(field, "lực bằng 0 (fx=fy=fz=0)",
                            "khai ít nhất một thành phần khác 0")
        out.append(Load3D(node=node, **comps))
    return tuple(out)


def _parse_supports3(raw, nx, ny, nz) -> tuple:
    if not isinstance(raw, list) or not raw:
        raise SpecError("supports", "phải là list không rỗng",
                        "không có ngàm → rigid body, không giải được")
    out = []
    for i, entry in enumerate(raw):
        field = f"supports[{i}]"
        if not isinstance(entry, dict):
            raise SpecError(field, "mỗi mục phải là object", "")
        dof = entry.get("dof", "all")
        if dof not in VALID_DOFS3:
            raise SpecError(f"{field}.dof",
                            f"phải thuộc {VALID_DOFS3}, nhận {dof!r}", "")
        if "face" in entry:
            nodes = _face_nodes(entry["face"], nx, ny, nz, field)
        else:
            nodes = [_resolve_node3(entry, nx, ny, nz, field)]
        out.extend(Support3D(node=n, dof=dof) for n in nodes)
    return tuple(out)


def _parse_primitives(raw, name: str, nx: int, ny: int, nz: int) -> tuple:
    if not isinstance(raw, list):
        raise SpecError(name, "phải là list (được phép rỗng)", "")
    prims = []
    for i, entry in enumerate(raw):
        field = f"{name}[{i}]"
        if not isinstance(entry, dict) or "type" not in entry:
            raise SpecError(field, "mỗi vùng phải là object có 'type'",
                            f"type thuộc {VALID_PRIMITIVES}")
        kind = entry["type"]
        if kind not in VALID_PRIMITIVES:
            raise SpecError(f"{field}.type",
                            f"phải thuộc {VALID_PRIMITIVES}, nhận {kind!r}", "")
        try:
            if kind == "box":
                p = tuple(int(entry[k]) for k in
                          ("x0", "y0", "z0", "x1", "y1", "z1"))
                x0, y0, z0, x1, y1, z1 = p
                if not (0 <= x0 <= x1 < nx and 0 <= y0 <= y1 < ny
                        and 0 <= z0 <= z1 < nz):
                    raise SpecError(field, f"box {p} ngoài lưới element "
                                    f"[0..{nx-1}]×[0..{ny-1}]×[0..{nz-1}]",
                                    "box tính theo lưới ELEMENT")
            elif kind == "sphere":
                p = tuple(float(entry[k]) for k in ("cx", "cy", "cz", "r"))
                cx, cy, cz, r = p
                if r <= 0:
                    raise SpecError(f"{field}.r", f"bán kính phải > 0, nhận {r}", "")
                if not (0 <= cx <= nx and 0 <= cy <= ny and 0 <= cz <= nz):
                    raise SpecError(field, f"tâm cầu ({cx},{cy},{cz}) ngoài lưới", "")
            else:  # cylinder
                axis = entry.get("axis")
                if axis not in VALID_AXES:
                    raise SpecError(f"{field}.axis",
                                    f"phải thuộc {VALID_AXES}, nhận {axis!r}", "")
                perp = [a for a in ("x", "y", "z") if a != axis]
                c1 = float(entry[f"c{perp[0]}" if False else f"c{perp[0]}"])
                c2 = float(entry[f"c{perp[1]}"])
                r = float(entry["r"])
                a0 = int(entry[f"{axis}0"])
                a1 = int(entry[f"{axis}1"])
                lim = {"x": nx, "y": ny, "z": nz}[axis]
                if r <= 0:
                    raise SpecError(f"{field}.r", f"bán kính phải > 0, nhận {r}", "")
                if not (0 <= a0 <= a1 < lim):
                    raise SpecError(field, f"khoảng trục [{a0},{a1}] ngoài "
                                    f"[0..{lim-1}]", "")
                p = (axis, c1, c2, r, a0, a1)
        except KeyError as exc:
            raise SpecError(field, f"thiếu trường {exc.args[0]!r} cho {kind}",
                            "xem spec stage1-t1 mục 2") from exc
        prims.append(Primitive(kind=kind, params=p))
    return tuple(prims)


def load_spec3d(path) -> Spec3D:
    """Đọc + validate spec.json schema v1 (3D). Trả về Spec3D bất biến."""
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
    for name in _REQUIRED:
        if name not in raw:
            raise SpecError(name, "trường bắt buộc bị thiếu",
                            f"khai \"{name}\" trong spec.json (schema v1)")

    nx = _require_int(raw, "nelx", 1)
    ny = _require_int(raw, "nely", 1)
    nz = _require_int(raw, "nelz", 1)
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

    return Spec3D(
        nelx=nx, nely=ny, nelz=nz, volfrac=volfrac,
        loads=_parse_loads3(raw["loads"], nx, ny, nz),
        supports=_parse_supports3(raw["supports"], nx, ny, nz),
        E=e_mod, nu=nu, p=p_pen, rmin=rmin,
        preserve=_parse_primitives(raw["preserve"], "preserve", nx, ny, nz),
        void=_parse_primitives(raw["void"], "void", nx, ny, nz))
