"""Material Database — Module 4 hợp đồng gốc.

Đọc materials.json (root repo), validate khoảng vật lý, tra theo tên.
Đơn vị LUÔN ghi trong tên trường: E_MPa, yield_MPa, density_kg_m3 —
đối sách S2-R2 (bug đơn vị kinh điển của ngành).
"""

from __future__ import annotations

import json
from pathlib import Path

from geophys.errors import SpecError

_DEFAULT_PATH = Path(__file__).resolve().parents[1] / "materials.json"
_REQUIRED_FIELDS = ("E_MPa", "nu", "yield_MPa")


def load_materials(path=None) -> dict:
    """Đọc + validate toàn bộ database. Lỗi nêu đúng vật liệu + trường."""
    p = Path(path) if path is not None else _DEFAULT_PATH
    if not p.is_file():
        raise SpecError("materials.json",
                        f"không tìm thấy database tại {p}",
                        "file phải nằm ở root repo")
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SpecError("materials.json",
                        f"JSON hỏng tại dòng {exc.lineno}: {exc.msg}",
                        "kiểm tra dấu phẩy / ngoặc") from exc

    db = {}
    for name, entry in raw.items():
        if name.startswith("_"):
            continue  # trường chú thích
        field = f"materials.json[{name}]"
        if not isinstance(entry, dict):
            raise SpecError(field, "mỗi vật liệu phải là object", "")
        for key in _REQUIRED_FIELDS:
            if key not in entry:
                raise SpecError(f"{field}.{key}", "trường bắt buộc bị thiếu",
                                f"cần đủ {_REQUIRED_FIELDS}")
            val = entry[key]
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise SpecError(f"{field}.{key}",
                                f"phải là số, nhận {val!r}", "")
        if entry["E_MPa"] <= 0:
            raise SpecError(f"{field}.E_MPa",
                            f"phải > 0, nhận {entry['E_MPa']}", "")
        if not (0.0 < entry["nu"] < 0.5):
            raise SpecError(f"{field}.nu",
                            f"phải trong (0, 0.5), nhận {entry['nu']}", "")
        if entry["yield_MPa"] <= 0:
            raise SpecError(f"{field}.yield_MPa",
                            f"phải > 0, nhận {entry['yield_MPa']}", "")
        db[name] = dict(entry)
    if not db:
        raise SpecError("materials.json", "database rỗng", "")
    return db


def get_material(name: str, path=None) -> dict:
    """Tra một vật liệu theo tên khóa. Tên lạ → SpecError kèm danh sách."""
    db = load_materials(path)
    if name not in db:
        raise SpecError("material_name",
                        f"không có vật liệu {name!r} trong database",
                        "tên có sẵn: " + ", ".join(sorted(db)))
    return db[name]
