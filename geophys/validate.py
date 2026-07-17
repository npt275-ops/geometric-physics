"""Spec Validator máy-đọc-được — Tầng 3.1 (DoD-3.2).

MỘT NGUỒN SỰ THẬT: mọi luật nằm trong load_spec3d + Grid3D (STABLE).
Module này chỉ (1) bắt SpecError và dịch sang JSON {mã, vị trí, lý do,
gợi ý} cho agent TỰ SỬA spec, (2) thêm duy nhất kiểm KHẢ THI THỂ TÍCH
mà pipeline chạy thật mới lộ ra (preserve chiếm quá volfrac).

Hợp đồng: validate_spec KHÔNG raise với spec rác — trả dict lỗi.
"""

from __future__ import annotations

from geophys.errors import SpecError
from geophys.grid3d import Grid3D
from geophys.spec3d import load_spec3d

# Map field(SpecError) → mã lỗi ổn định cho agent. Field không khớp
# nhóm nào → GP-E-SCHEMA (an toàn: agent đọc ly_do/goi_y).
_MA_THEO_TRUONG = (
    ("GP-E-FILE", ("file",)),
    ("GP-E-JSON", ("json",)),
    ("GP-E-PHYSICS", ("supports", "loads", "load_cases",
                      "loads/load_cases", "volfrac")),
    ("GP-E-GEOMETRY", ("preserve", "void", "preserve/void")),
)


def _ma_loi(field: str) -> str:
    goc = field.split(".")[0]
    for ma, truong_list in _MA_THEO_TRUONG:
        for t in truong_list:
            if goc == t or goc.startswith(t):
                return ma
    return "GP-E-SCHEMA"


def _loi(exc: SpecError) -> dict:
    return {"ma": _ma_loi(exc.field), "vi_tri": exc.field,
            "ly_do": exc.reason,
            "goi_y": exc.hint or "xem docs/spec_schema.json"}


def validate_spec(path, deep: bool = True) -> dict:
    """Kiểm spec 3D (v1/v2). Trả dict JSON-able, không raise với rác."""
    loi = []
    spec = None
    try:
        spec = load_spec3d(path)
    except SpecError as exc:
        loi.append(_loi(exc))

    grid = None
    if spec is not None and deep:
        try:
            grid = Grid3D(spec)
        except SpecError as exc:
            loi.append(_loi(exc))

    canh_bao = []
    if grid is not None:
        # Kiểm MỚI duy nhất: khả thi thể tích. OC không thể đạt volfrac
        # nếu riêng vùng preserve đã chiếm nhiều hơn ngân sách vật liệu.
        n_el = spec.nelx * spec.nely * spec.nelz
        n_preserve = int(grid.preserve_mask.sum())
        if 0.7 * spec.volfrac * n_el < n_preserve <= spec.volfrac * n_el:
            # Gauntlet bai08 16/07/2026: preserve ~89% ngân sách làm OC
            # phải giảm chấn, thiết kế kém tối ưu. Cảnh báo mềm — không chặn.
            canh_bao.append({
                "ma": "GP-W-PHYSICS", "vi_tri": "preserve/volfrac",
                "ly_do": (f"vùng bảo tồn chiếm {n_preserve / (spec.volfrac * n_el):.0%} "
                          "ngân sách vật liệu (>70%) — ít tự do tối ưu, "
                          "kết quả có thể kém cứng"),
                "goi_y": "tăng volfrac hoặc thu nhỏ preserve nếu có thể"})
        if n_preserve > spec.volfrac * n_el:
            loi.append({
                "ma": "GP-E-PHYSICS", "vi_tri": "preserve/volfrac",
                "ly_do": (f"vùng bảo tồn chiếm {n_preserve}/{n_el} voxel "
                          f"({n_preserve / n_el:.1%}) > volfrac "
                          f"{spec.volfrac:.1%} — bài toán bất khả thi"),
                "goi_y": "tăng volfrac hoặc thu nhỏ vùng preserve"})

    ket_qua = {
        "trang_thai": "HOP_LE" if not loi else "KHONG_HOP_LE",
        "loi": loi,
        "canh_bao": canh_bao,
    }
    if not loi:
        so_case = len(spec.load_cases)
        ket_qua["tom_tat"] = {
            "luoi": f"{spec.nelx}x{spec.nely}x{spec.nelz}",
            "so_phan_tu": spec.nelx * spec.nely * spec.nelz,
            "so_case": so_case,
            "vat_lieu": spec.material_name or "E,nu tự khai",
            "volfrac": spec.volfrac,
        }
    return ket_qua
