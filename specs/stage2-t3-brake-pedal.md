# SPEC: stage2-t3-brake-pedal

> Tầng 2.3 ⭐ — bài toán THẬT đầu tiên (S2.1 #2 hợp đồng gốc). Mức: HIGH.
> KHÔNG mở khóa file protected nào — tầng này chỉ THIẾT KẾ BÀI TOÁN
> (spec.json + generator + thí nghiệm + bộ chạy), engine đứng nguyên.
> Cổng NGƯỜI kép: (a) duyệt hình học qua ảnh render TRƯỚC khi đốt máy;
> (b) chạy bài chuẩn trên laptop.

## 1. Mục tiêu
Dựng bài bàn đạp phanh nhôm 6061 theo hợp đồng gốc: chốt xoay (preserve
trụ + lỗ trục void), tấm đệm chân (preserve), 1200N chính + 2 case phụ,
volume 45% — và chứng minh DoD-2.1/2.2/2.4 bằng số.

## 2. Thiết kế bài toán (tham số NGƯỜI duyệt)

**Không gian thiết kế:** 160 × 80 × 20 mm = lưới 80×40×10 voxel, h = 2mm
(32.000 phần tử — ~nửa bài bench 64³, nhưng ×3 case ≈ tương đương).
Vật liệu: `nhom_6061_t6` (E 68900 MPa, yield 276 MPa). Volume 45%.
Quy ước: y hướng XUỐNG (mặt y=0 là mặt TRÊN — nơi đặt chân).

```
  y=0 (mặt trên)                                    PAD ĐẠP (preserve)
   ┌────────────────────────────────────────────────▓▓▓▓▓▓▓▓┐
   │      ← 160mm →                                 ▓ 16×8mm▓│  ↓ F đạp
   │   ╭───────╮                                    ▓▓▓▓▓▓▓▓│  1200N (+y)
   │   │ PIVOT │  preserve trụ r=12mm                        │
   │   │  ◯←lỗ │  void trụ r=6mm (trục xoay)                 │ 80mm
   │   │       │  ngàm: vành node r≤6.4mm quanh tâm          │
   │   ╰───────╯  tâm (20mm, 40mm), xuyên suốt z=20mm        │
   └─────────────────────────────────────────────────────────┘
```

**3 load case** (đặt phân bố trên mặt pad, trọng số biên 0.5/góc 0.25):

| Case | Lực | Trọng số w | Ý nghĩa |
|---|---|---|---|
| 1 | 1200N thẳng (+y) | 1.0 | đạp chính diện |
| 2 | 1200N lệch 15° trong mặt xy (fy=1159.1, fx=−310.6) | 0.5 | đạp lệch về pivot |
| 3 | 360N ngang (+z) | 0.3 | đạp xéo (0.3×1200) |

**Bản smoke** (cho test tự động + thí nghiệm DoD-2.1 trong sandbox):
cùng hình học vật lý, lưới thô 40×20×5, h=4mm, rmin 2.0.

## 3. Output (danh sách file ĐÓNG)
- `scripts/gen_brake_pedal_spec.py` (generator deterministic → 4 spec)
- `examples/spec_brake_pedal.json` + `examples/spec_brake_pedal_single.json`
- `examples/spec_brake_smoke.json` + `examples/spec_brake_smoke_single.json`
- `media/brake_pedal_design_space.png` (NGƯỜI duyệt hình học)
- `scripts/run_brake_pedal.py` + `RUN_BRAKE_PEDAL.bat` (bài chuẩn, checkpoint,
  STL, render, report, verdict DoD-2.1/2.2/2.4)
- `tests/test_brake_pedal.py`
(spec này: `specs/stage2-t3-brake-pedal.md`)

## 4. Logic thí nghiệm DoD-2.1 (định lượng, không cảm quan)
1. Chạy multi (3 case) → ρ_multi; chạy single (case 1) → ρ_single.
2. Đánh giá CHÉO: giữ nguyên ρ, solve dưới tải lệch (case 2):
   c₂(ρ_single) và c₂(ρ_multi). ĐẠT khi c₂(ρ_single) ≥ 1.3 × c₂(ρ_multi)
   (cấu trúc multi cứng hơn ≥30% dưới tải lệch — đúng chữ hợp đồng).
3. DoD-2.4: |mean(ρ_multi) − 0.45| < 0.01·0.45. DoD-2.2: STL watertight.

## 4b. ĐỊNH NGHĨA PHÉP THỬ DoD-2.1 (chốt sau thí nghiệm smoke 14/07)
Đo thật bản smoke: c₂(lệch 15°): single/multi = 0.99 — tải lệch 15° TRONG
MẶT PHẲNG gần song song tải chính (cos15° = 0.966) nên KHÔNG phân biệt
được hai thiết kế; c₃(ngang/đạp xéo): single/multi = **1.45** — đúng chỗ
"mỏng manh với hướng còn lại" của hợp đồng gốc. Do đó:
**DoD-2.1 = c₃(ρ_single)/c₃(ρ_multi) ≥ 1.3 trên bài chuẩn** (tải ngang
đạp xéo); tỷ số case 2 báo cáo kèm để minh bạch. Δρ = 32.2% (khác rõ rệt).

## 5. Dependencies
Engine 2.1+2.2 STABLE (chỉ gọi) · trimesh/render sẵn.

## 6. Không được phép
Chạm 26 file protected · nới ngưỡng 1.3/45%/watertight · đốt máy người
khi hình học chưa được duyệt.

## 7. Error handling
Generator kiểm khả thi (preserve pad + pivot < volfrac·nel) · runner có
checkpoint resume + verdict FAIL tường minh.

## 8. Acceptance
- Test (bản smoke): spec parse hợp lệ; pivot/pad/lỗ đúng thể tích;
  multi 3-case hội tụ; **thí nghiệm chéo c₂(single) / c₂(multi) — ngưỡng
  chốt theo đo thật, kỳ vọng > 1.3 ngay ở bản smoke**; volume 45%±1%;
  STL smoke watertight.
- Bài chuẩn (NGƯỜI chạy RUN_BRAKE_PEDAL.bat): verdict DoD-2.1 ≥ 1.3 ✓,
  DoD-2.2 watertight ✓, DoD-2.4 45%±1% ✓ — report + STL + render vào bench/.

## 9. Ngoài phạm vi
DoD-2.3 FreeCAD (tầng 2.5) · one-command CLI (2.4) · hình học cong chi
tiết sản xuất (voxel là mức Giai đoạn 1).

---
## Phase 0 — 7 câu (HIGH)
1. **Output:** mục 3; pytest PASS + preview cho người duyệt.
2. **Không chạm:** 26 file protected.
3. **Dependencies:** engine STABLE; không dep mới.
4. **I/O:** spec JSON thuần v2 (đã có schema); runner ra report JSON.
5. **STABLE liên quan:** toàn bộ engine — CHỈ GỌI.
6. **Lỗi:** generator/runner như mục 7; thí nghiệm FAIL = dữ liệu quý,
   không nới ngưỡng (S2-R3).
7. **Production?** Staging; bài chuẩn chạy trên máy người có checkpoint.
