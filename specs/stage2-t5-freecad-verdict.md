# SPEC: stage2-t5-freecad-verdict

> Tầng 2.5 ⭐⭐ — DoD-2.3 TỐI THƯỢNG (nguyên văn hợp đồng gốc): "Nạp STL bàn
> đạp phanh vào FreeCAD FEM/Ansys, đặt tải 1200N + điều kiện biên gốc.
> Kết quả: ứng suất Von Mises lớn nhất < giới hạn chảy của vật liệu (với
> nhôm 6061: < 276 MPa), không vùng phá hủy. Chụp màn hình + lưu file phân
> tích làm bằng chứng. Đây là khoảnh khắc Cấp độ 1 được tuyên bố thành công."
> Mức: HIGH · cổng NGƯỜI ký. KHÔNG mở khóa protected.

## 1. Mục tiêu
Macro FreeCAD tự động dựng phiên tòa: STL bàn đạp → SCALE về mm thật
(×element_size_mm — STL GP ở tọa độ voxel) → Solid → nhôm 6061 THẬT
→ ngàm mặt lỗ trục → 1200N lên pad → Gmsh → CalculiX → Von Mises
→ VERDICT so 276 MPa + safety factor. NGƯỜI nhìn màu + ký.

## 2. Thiết lập phiên tòa (đúng "tải + BC gốc")
- STL: `media/brake_pedal.stl` (kết quả DoD-2.1/2.2/2.4 đã đóng).
- Scale: ×2.0 (đọc từ examples/spec_brake_pedal.json → element_size_mm).
  Guard: sau scale, bề dài bbox phải ≈160mm — lệch >5% thì DỪNG báo lỗi.
- Vật liệu: E=68900 MPa, ν=0.33, ρ=2700 kg/m³ (materials.json — nhôm 6061-T6).
- Ngàm: các mặt có tâm cách trục pivot (20mm, 40mm) ≤ 7.5mm trong mặt xy
  (mặt trong lỗ trục — mô phỏng trục cứng, đúng BC bài GP).
- Tải: 1200N hướng +y (đạp), phân trên các mặt thuộc mặt trên (y≈min)
  vùng pad (x ≥ 140mm) — đúng vị trí và hướng case chính của spec.
- (Case phụ lệch/ngang đã được phân xử ở DoD-2.1; DoD-2.3 nguyên văn chỉ
  đòi tải 1200N chính.)

## 3. Output (danh sách file ĐÓNG)
- `scripts/freecad_brake_verdict.py` (macro ASCII — bài học encoding 1.5)
- `RUN_FREECAD_VERDICT.bat` (goto-style, log ra file — bài học bat 1.5)
- Bằng chứng do NGƯỜI sinh: `bench/freecad_brake_verdict.json` +
  `bench/brake_pedal_verdict.FCStd` + screenshot Von Mises
(spec này: `specs/stage2-t5-freecad-verdict.md`)

## 4. Verdict logic (máy đo — người ký)
- vm_max < 276 MPa VÀ không node nào vượt (đồng nghĩa) → "PASS-MAY".
- Report ghi: vm_max, vm_mean, vị trí max, safety_factor = 276/vm_max,
  n_nodes, các bước. Kèm tỷ số so sánh mốc tham khảo: bài GP nội bộ.
- NGƯỜI: mở FCStd, xem màu (nóng quanh lỗ trục/cổ chuyển tiếp là hợp lý),
  screenshot, tuyên bố "DoD-2.3 OK" — KHOẢNH KHẮC CẤP ĐỘ 1.
- Nếu FAIL (vm ≥ 276): theo S2-R3 — dữ liệu quý, quay lại xét volume/mesh
  /cách áp tải; KHÔNG nới 276.

## 5. Dependencies
FreeCAD 1.1.1 + CalculiX (đã chứng minh chạy được ở DoD-1.7) · STL 2.3.

## 6. Không được phép
Chạm 28 protected · nới 276 MPa · tự ký thay người (reality verification).

## 7. Error handling
Mọi bước ghi steps[]; lỗi → traceback đầy đủ vào report; scale guard DỪNG
sớm nếu kích thước sai; fallback API đa phiên bản như 1.5.

## 8. Acceptance
- Macro chạy trọn trên máy NGƯỜI: report status PASS-MAY, vm_max < 276,
  safety_factor ghi rõ, FCStd lưu.
- NGƯỜI xem màu + screenshot + tuyên bố "DoD-2.3 OK".
- Agent commit bằng chứng + BIÊN BẢN ĐÓNG STAGE 2 (6/6 DoD).

## 9. Ngoài phạm vi
Ansys (FreeCAD/CalculiX là trọng tài được hợp đồng chấp nhận) · mô phỏng
mỏi/va đập · tối ưu lại nếu PASS.

---
## Phase 0 — 7 câu (HIGH)
1. **Output:** macro + bat; bằng chứng từ máy người.
2. **Không chạm:** 28 protected.
3. **Dependencies:** pipeline FreeCAD đã thông ở 1.5 (Gmsh 2642 nodes,
   CalculiX OK, fallback API sẵn).
4. **I/O:** vào STL + spec (đọc scale); ra report JSON + FCStd.
5. **STABLE liên quan:** không sửa gì trong geophys.
6. **Lỗi:** mục 7; FAIL vật lý → quy trình S2-R3, không giấu.
7. **Production?** Đây là reality verification — bản chất tầng là kiểm.
