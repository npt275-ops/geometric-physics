# PROJECT MANIFEST — GEOMETRIC PHYSICS (GP)

> Bản đồ tĩnh. Agent đọc TRƯỚC TIÊN. MANIFEST sai làm agent tin sai.

## Thông tin dự án
- **Tên:** Geometric Physics (GP) · **Giai đoạn:** BUILDING (Stage 0 — lõi 2D)
- **Một câu:** Engine tối ưu hóa topology (FEA + SIMP + Filter + OC), Python,
  headless, nhận spec.json trả về cấu trúc tối ưu — kiểm chứng bằng benchmark
  quốc tế, không bằng cảm quan.
- **Tài liệu mẹ:** GEOMETRIC_PHYSICS_PLAN.txt (v1.0) + STAGE1_EXECUTION_PLAN.txt (v1.1)

## Tình trạng dự án (cập nhật 07/07/2026 — sau khi đóng Tầng 0.4)
- **Tiến độ Stage 0:** 4/6 tầng đóng (0.1 grid → 0.2 FEA → 0.3 sens/filter/OC
  → 0.4 vòng lặp + benchmark). Còn: 0.5 render (LOW), 0.6 CI (cần GitHub repo).
- **Cột mốc đã đạt — DoD-0.1 (cửa ải Stage 0):** MBB beam 60×20 hội tụ 94 vòng,
  compliance 203.1812 — lệch **0.006%** so với port top88 trung thực
  (ngưỡng ±5%). Bộ toán ĐÚNG với chuẩn quốc tế.
- **DoD đã xanh bằng test:** 0.1 ✓ · 0.2 (0 checkerboard) ✓ · 0.3 (94<200 vòng,
  đơn điệu) ✓ · 0.4 (preserve/void từng vòng, volume ±1%) ✓ · 0.5 (Static
  Physics, đóng ở Tầng 0.2) ✓ · 0.6 (deterministic từng bit) ✓.
  Còn: 0.7 (CI xanh — chờ GitHub) · 0.8 (GIF — Tầng 0.5).
- **Test:** 73/73 pass, ~2.7s. Mọi ngưỡng đều có số đo thật ghi trong docstring test.
- **Kỷ luật quy chuẩn:** 12 file protected + snapshot md5 · metrics 5 vòng
  postagent = 4 ĐÚNG-ngay-lần-1, 1 FAIL (scope-creep do file khóa Word — đã ignore).
- **Stage 1 (3D):** KHÓA cho đến khi 8/8 DoD Stage 0 xanh. Kế hoạch + phân tầng
  đo được: STAGE1_EXECUTION_PLAN.txt Phụ lục A.

## Thành phần STABLE (KHÔNG được sửa — phải có trong .sammis/protected.list)
| File / Module | Trạng thái | Mô tả |
|---|---|---|
| GEOMETRIC_PHYSICS_PLAN.txt | STABLE | Kế hoạch gốc v1.0 — hợp đồng dự án |
| STAGE1_EXECUTION_PLAN.txt | STABLE | Kế hoạch thực thi Stage 1 v1.1 + Phụ lục A |
| AGENT_RULES.md | STABLE | Quy chuẩn agent — không sửa |
| sammis.py | STABLE | Trạm gác — không sửa |
| geophys/errors.py | STABLE | SpecError — Tầng 0.1 đóng 07/07/2026, 32/32 test |
| geophys/spec_loader.py | STABLE | Schema v0 loader — Tầng