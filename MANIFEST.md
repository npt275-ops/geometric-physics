# PROJECT MANIFEST — GEOMETRIC PHYSICS (GP)

> Bản đồ tĩnh. Agent đọc TRƯỚC TIÊN. MANIFEST sai làm agent tin sai.

## Thông tin dự án
- **Tên:** Geometric Physics (GP) · **Giai đoạn:** BUILDING (Stage 0 — lõi 2D)
- **Một câu:** Engine tối ưu hóa topology (FEA + SIMP + Filter + OC), Python,
  headless, nhận spec.json trả về cấu trúc tối ưu — kiểm chứng bằng benchmark
  quốc tế, không bằng cảm quan.
- **Tài liệu mẹ:** GEOMETRIC_PHYSICS_PLAN.txt (v1.0) + STAGE1_EXECUTION_PLAN.txt (v1.1)

## Thành phần STABLE (KHÔNG được sửa — phải có trong .sammis/protected.list)
| File / Module | Trạng thái | Mô tả |
|---|---|---|
| GEOMETRIC_PHYSICS_PLAN.txt | STABLE | Kế hoạch gốc v1.0 — hợp đồng dự án |
| STAGE1_EXECUTION_PLAN.txt | STABLE | Kế hoạch thực thi Stage 1 v1.1 + Phụ lục A |
| AGENT_RULES.md | STABLE | Quy chuẩn agent — không sửa |
| sammis.py | STABLE | Trạm gác — không sửa |
| geophys/errors.py | STABLE | SpecError — Tầng 0.1 đóng 07/07/2026, 32/32 test |
| geophys/spec_loader.py | STABLE | Schema v0 loader — Tầng 0.1 đóng |
| geophys/grid2d.py | STABLE | Lưới 2D + edof + mật độ — Tầng 0.1 đóng |
| geophys/fea2d.py | STABLE | FEA Q4 sparse + energy — Tầng 0.2 đóng 07/07/2026, KE khớp Gauss 1e-16, Timoshenko 0.75% |

## Thành phần IN PROGRESS
| File / Module | Đang làm gì |
|---|---|
| (kế tiếp: specs/stage0-t3-sens-filter-oc.md) | |

## Thành phần NOT BUILT (CHƯA TỒN TẠI — ĐỪNG IMPORT)
| File / Module | Ghi chú |
|---|---|
| geophys/sensitivity.py | Stage 0 task 3 |
| geophys/filter2d.py | Stage 0 task 3 |
| geophys/oc_update.py | Stage 0 task 3 |
| geophys/optimize.py (vòng lặp) | Stage 0 task 4 |
| geophys/render2d.py | Stage 0 task 5 |
| geophys/grid3d.py, fea3d.py, filter3d.py | Stage 1 — chỉ mở khi Stage 0 đóng 8/8 DoD |
| geophys/checkpoint.py | Stage 1 |
| geophys/export_stl.py | Stage 1 (Block E) |
| geophys/render3d.py, viewer HTML | Stage 1 (Block F — optional) |
| CLI geophys, spec validator, agent interface | Stage 3 — CẤM đụng trước đó |
