# SPEC: stage3-t1-validator

> Tầng 3.1 — Spec Validator máy-đọc-được + `geophys validate` (S3.1 #1-2,
> DoD-3.2). Mức: MEDIUM. Mở khóa: geophys/__main__.py (tầng 3.2 chung
> nghi thức). Engine đứng nguyên.

## 1. Mục tiêu
Agent gửi spec rác phải nhận về JSON lỗi đọc-được-bằng-máy (mã + vị trí
+ gợi ý sửa) để TỰ SỬA — không traceback, không tiếng người mơ hồ.

## 2. Thiết kế
- `geophys/validate.py`: `validate_spec(path, deep=True) -> dict`
  {trang_thai HOP_LE|KHONG_HOP_LE, loi:[{ma, vi_tri, ly_do, goi_y}],
   tom_tat{luoi, so_phan_tu, so_case, vat_lieu, volfrac} khi hợp lệ}.
- MỘT NGUỒN SỰ THẬT (S3-R1): gọi load_spec3d + Grid3D, dịch SpecError
  → mã. KHÔNG viết lại luật. Thêm DUY NHẤT kiểm mới: khả thi thể tích
  (preserve > volfrac·nel ⇒ GP-E-PHYSICS).
- Mã lỗi: GP-E-FILE / GP-E-JSON / GP-E-SCHEMA (thiếu trường, sai kiểu,
  sai miền) / GP-E-GEOMETRY (ngoài lưới, giao nhau) / GP-E-PHYSICS
  (lực 0, thiếu ngàm, bất khả thi) — map theo field của SpecError.
- `docs/spec_schema.json`: JSON Schema draft-07 đầy đủ v1+v2 (tài liệu
  cho agent; không thêm dependency jsonschema — loader vẫn là luật).

## 3. Output (ĐÓNG)
geophys/validate.py · docs/spec_schema.json · tests/test_validator.py ·
spec này. (CLI wiring → tầng 3.2.)

## 4. Logic thí nghiệm DoD-3.2
10 spec cố tình sai (đúng lời hợp đồng: thiếu ngàm, lực=0, preserve
ngoài lưới, volume>1 + 6 kiểu khác): validator bắt 10/10, mỗi lỗi có
đủ ma/vi_tri/ly_do và goi_y không rỗng cho lỗi schema/physics.
Spec hợp lệ (smoke bàn đạp) → HOP_LE + tom_tat đúng.

## 5. Dependencies
spec3d + grid3d STABLE (chỉ gọi).

## 6. Không được phép
Sửa luật trong loader · nới bất kỳ ngưỡng · dependency mới.

## 7. Error handling
validate_spec KHÔNG raise với spec rác — trả dict lỗi; chỉ raise với
bug nội bộ thật (để lộ, không nuốt).

## 8. Acceptance
pytest tests/test_validator.py: 10/10 rác bị bắt đúng mã; spec chuẩn
HOP_LE; mọi lỗi có goi_y actionable; không đổi golden/145+ test cũ.

## 9. Ngoài phạm vi
CLI (3.2) · agent trials (3.3) · spec 2D (engine đóng hộp = 3D).

---
## Phase 0 — 7 câu (MEDIUM)
1. Output: mục 3. 2. Không chạm: 28 protected (giai đoạn này).
3. Dep: không mới. 4. I/O: path → dict JSON-able. 5. STABLE: chỉ gọi.
6. Lỗi: mục 7. 7. Production? Staging — agent-facing API.
