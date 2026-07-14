# PROJECT MANIFEST — GEOMETRIC PHYSICS (GP)

> Bản đồ tĩnh. Agent đọc TRƯỚC TIÊN. MANIFEST sai làm agent tin sai.

## Thông tin dự án
- **Tên:** Geometric Physics (GP) · **Giai đoạn:** BUILDING (Stage 2 — bài toán thật; STAGE 1 ĐÓNG 12/07/2026)
- **Một câu:** Engine tối ưu hóa topology (FEA + SIMP + Filter + OC), Python,
  headless, nhận spec.json trả về cấu trúc tối ưu — kiểm chứng bằng benchmark
  quốc tế, không bằng cảm quan.
- **Tài liệu mẹ:** GEOMETRIC_PHYSICS_PLAN.txt (v1.0) + STAGE1_EXECUTION_PLAN.txt (v1.1)

## Tình trạng dự án (cập nhật 08/07/2026 — STAGE 0 ĐÓNG 8/8 DoD)
- **STAGE 0 ĐÓNG 8/8 DoD** (08/07/2026, CI 4/4 xanh).
- **STAGE 1 ĐÓNG 7/7 DoD (12/07/2026)** — người vận hành ký DoD-1.7:
  1.1 benchmark 0.028% vs ref (54 vòng) · 1.2 hội tụ 115 vòng/25 phút laptop
  thật · 1.3 peak RAM 718MB · 1.4 resume giống hệt từng bit (direct+CG) ·
  1.5 đối xứng <1% · 1.6 2D nguyên vẹn (145 test) · 1.7 FreeCAD+CalculiX:
  Von Mises max 76.62 MPa tại x=11.6 GẦN ngàm, bằng chứng bench/ (FCStd +
  report + screenshot). DoD-1.8 (optional) viewer ✓. STAGE 2: 3/5 tầng — 2.3 BÀN ĐẠP PHANH ĐÓNG 14/07 trên laptop thật:
  multi 65 vòng (c=275.90) · single 141 vòng · DoD-2.1 tỷ số đạp xéo
  **1.923 ≥ 1.3** (single yếu hơn 92%) · DoD-2.2 STL watertight ·
  DoD-2.4 volume 0.45000. Evidence bench/ + media/brake_pedal.stl.
  Người vận hành duyệt hình học bằng lệnh chạy bài chuẩn. Kế tiếp: 2.4.
- **Cột mốc đã đạt — DoD-0.1 (cửa ải Stage 0):** MBB beam 60×20 hội tụ 94 vòng,
  compliance 203.1812 — lệch **0.006%** so với port top88 trung thực
  (ngưỡng ±5%). Bộ toán ĐÚNG với chuẩn quốc tế.
- **DoD đã xanh bằng test:** 0.1 ✓ · 0.2 (0 checkerboard) ✓ · 0.3 (94<200 vòng,
  đơn điệu) ✓ · 0.4 (preserve/void từng vòng, volume ±1%) ✓ · 0.5 (Static
  Physics, đóng ở Tầng 0.2) ✓ · 0.6 (deterministic từng bit) ✓.
  0.7 (CI 4/4 xanh, người xác nhận 08/07) ✓ · 0.8 (GIF 94 khung) ✓ — ĐỦ 8/8.
- **Test:** 79/79 pass, ~2.7s. Mọi ngưỡng đều có số đo thật ghi trong docstring test.
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
| geophys/spec_loader.py | STABLE | Schema v0 loader — Tầng 0.1 đóng |
| geophys/grid2d.py | STABLE | Lưới 2D + edof + mật độ — Tầng 0.1 đóng |
| geophys/fea2d.py | STABLE | FEA Q4 sparse + energy — Tầng 0.2 đóng 07/07/2026, KE khớp Gauss 1e-16, Timoshenko 0.75% |
| geophys/sensitivity.py | STABLE | ∂c/∂ρ — Tầng 0.3 đóng, FD check 4.1e-06 |
| geophys/filter2d.py | STABLE | Sensitivity filter conv — Tầng 0.3 đóng, khớp ref O(N²) 2.7e-15 |
| geophys/oc_update.py | STABLE | OC bisection — Tầng 0.3 đóng, vol err 3.6e-08 |
| geophys/optimize.py | STABLE | Vòng lặp tối ưu — Tầng 0.4 đóng, MBB khớp top88 0.006%, DoD-0.1 ✓ |
| geophys/render2d.py | STABLE | PNG/GIF tách rời engine — Tầng 0.5 đóng, DoD-0.8 ✓ (media/) |
| .github/workflows/ci.yml | STABLE | CI matrix 4 ô — DoD-0.7 xanh 08/07/2026 |
| geophys/spec3d.py | STABLE | Schema v1+v2 (load_cases, material_name, element_size_mm; E=E_MPa×h) — golden giữ nguyên qua 2.1+2.2 |
| materials.json | STABLE | DB vật liệu: nhôm 6061 yield 276 MPa (khớp DoD-2.3), Ti-6Al-4V, thép S235 |
| geophys/materials.py | STABLE | Load + validate + tra vật liệu — Tầng 2.2 |
| geophys/grid3d.py | STABLE | Voxel H8 + rasterize (sphere 1.46%, cyl 1.34%) — Tầng 1.1 đóng |
| geophys/fea3d.py | STABLE | FEA H8 + CG/direct + đa vector lực — 1.2 đóng, 2.1 mở rộng, golden giữ nguyên |
| geophys/sensitivity3d.py | STABLE | ∂c/∂ρ 3D — Tầng 1.3 đóng, FD 1.8e-07 |
| geophys/filter3d.py | STABLE | Filter kernel cầu — Tầng 1.3 đóng, khớp ref 1.8e-15 |
| geophys/optimize3d.py | STABLE | Vòng lặp 3D multi-load Σwᵢcᵢ + checkpoint — DoD-1.1 0.028%, golden trùng bit sau 2.1 |
| geophys/checkpoint.py | STABLE | Save/load + digest chống resume nhầm bài — Tầng 1.4 |
| geophys/export_stl.py | STABLE | Marching cubes + Taubin + trimesh check — Tầng 1.5: box 4.36%, sphere 0.88% |
| geophys/render3d.py | STABLE | PNG trisurf + HTML viewer tự chứa offline — Tầng 1.6, DoD-1.8 ✓ |

## Thành phần IN PROGRESS
| File / Module | Đang làm gì |
|---|---|
| specs/stage2-t4-run-cli.md | Tầng 2.4 — one-command spec→STL (kế tiếp) |

## Thành phần NOT BUILT (CHƯA TỒN TẠI — ĐỪNG IMPORT)
| File / Module | Ghi chú |
|---|---|
| CLI geophys, spec validator, agent interface | Stage 3 — CẤM đụng trước đó |
