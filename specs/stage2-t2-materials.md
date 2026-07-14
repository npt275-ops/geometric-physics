# SPEC: stage2-t2-materials

> Tầng 2.2 Stage 2 — vật liệu thật + đơn vị thật. Mức: HIGH → đủ 7 câu.
> Từ đây con số "276 MPa" của DoD-2.3 mới có nghĩa vật lý.
>
> **ĐỀ XUẤT MỞ KHÓA:** chỉ `geophys/spec3d.py` (thêm trường v2).
> **KHÔNG đụng fea3d/optimize3d** nhờ đẳng thức K = E·h·K_unit (H8 lập
> phương cạnh h): nạp E_engine = E_MPa × h_mm ngay ở loader là toàn hệ
> tự động đúng đơn vị mm-N-MPa. Golden tầng 2.1 tiếp tục là trọng tài.

## 1. Mục tiêu
`materials.json` (Nhôm 6061-T6, Ti-6Al-4V, Thép S235: E_MPa, nu, yield_MPa,
density) + spec v2 nhận `material_name` và `element_size_mm` → toàn pipeline
chạy đơn vị thật: lực N, kích thước mm, ứng suất MPa, compliance N·mm.

## 2. Input — mở rộng schema v2
- `element_size_mm` (tùy chọn, float > 0, mặc định 1.0 = chế độ đơn vị hóa cũ).
- `material_name` (tùy chọn, string, tra materials.json) XOR `material`
  (inline {E, nu} như cũ — E hiểu là MPa khi có element_size_mm).
  Cả hai → SpecError; không cái nào → SpecError.
- materials.json entry bắt buộc: E_MPa > 0, 0 < nu < 0.5, yield_MPa > 0.

## 3. Output (danh sách file ĐÓNG)
- `materials.json` (root — đúng tên Module 4 hợp đồng gốc)
- `geophys/materials.py` (load + validate + get_material)
- `geophys/spec3d.py` (SỬA: element_size_mm, material_name, e_mpa,
  yield_mpa; E_engine = e_mpa × element_size_mm)
- `tests/test_materials.py`
(spec này: `specs/stage2-t2-materials.md`)

## 4. Logic
1. materials.py: đọc JSON UTF-8, validate từng vật liệu (khoảng vật lý),
   tên lạ → SpecError kèm danh sách tên có sẵn.
2. spec3d: parse 2 trường mới; Spec3D thêm field mặc định (spec cũ không
   đổi hành vi — golden canh); E = e_mpa × element_size_mm.
3. Legacy (không element_size_mm, material inline): h=1, E nguyên trạng —
   TỪNG BIT như trước.

## 5. Dependencies
Không dep mới. Golden G1/G2 (test_multiload) là trọng tài hồi quy.

## 6. Không được phép
Chạm fea3d/optimize3d/23 file protected còn lại · đổi golden constants ·
đưa ứng suất-stress vào engine (phạm vi đóng — trọng tài là FreeCAD).

## 7. Error handling
materials.json hỏng/thiếu trường → SpecError nêu vật liệu + trường ·
material_name lạ → SpecError kèm danh sách · element_size_mm ≤ 0 → SpecError.

## 8. Acceptance
- **Luật scaling E (giải tích):** E×2, cùng bài → U giảm đúng 2 lần,
  c giảm đúng 2 lần (rtol 1e-12).
- **Luật scaling h (giải tích):** element_size_mm 2.0 vs 1.0 → U và c
  giảm đúng h lần (K ∝ h) (rtol 1e-12).
- **Đơn vị tuyệt đối vs Timoshenko:** dầm nhôm 6061 THẬT (E=68900 MPa),
  kích thước mm, lực N → độ võng đầu dầm [mm] khớp công thức < 5%.
- **Golden G1/G2 vẫn trùng bit** (spec cũ không element_size_mm).
- **DB:** 3 vật liệu tra được; nhôm 6061 yield ĐÚNG 276 MPa (khớp hợp đồng
  gốc); tên lạ → SpecError liệt kê tên; entry hỏng → SpecError.
- **XOR:** material + material_name cùng lúc → SpecError; thiếu cả hai →
  SpecError; element_size_mm = 0/âm → SpecError.

## 9. Ngoài phạm vi
Bàn đạp phanh (2.3) · CLI (2.4) · tự tính Von Mises trong engine (đóng).

---
## Phase 0 — 7 câu (HIGH)
1. **Output:** mục 3; pytest PASS + golden trùng.
2. **Không chạm:** 23 protected còn lại (spec3d mở khóa nghi thức).
3. **Dependencies:** không mới; suite 157 xanh.
4. **I/O:** Spec3D thêm 4 field mặc định; API cũ nguyên vẹn.
5. **STABLE liên quan:** fea3d đọc spec.E — đẳng thức E·h bảo toàn interface.
6. **Lỗi:** mục 7; golden lệch = dừng cứng.
7. **Production?** Staging; rollback git revert; digest checkpoint tự vô hiệu
   checkpoint cũ (an toàn — không resume nhầm hệ đơn vị).
