# PROJECT CONTEXT — GEOMETRIC PHYSICS

> Tri thức sâu, đọc SAU MANIFEST.

## 1. Naming convention
- Package: `geophys`. Module theo tầng: `grid2d`, `fea2d`, `grid3d`...
- Test: `tests/test_<module>.py`, mỗi con số đo được trong Phụ lục A
  của STAGE1_EXECUTION_PLAN.txt = ít nhất 1 pytest case.
- Spec bài toán mẫu: `examples/spec_<tên>_<kích thước>.json`.

## 2. Coding rules (bắt buộc)
- Mọi lỗi xử lý tường minh; cấm `except: pass`.
- Windows-first: `PYTHONUTF8=1`, mọi đường dẫn qua `pathlib.Path`,
  mọi `open()` có `encoding="utf-8"`. (Bài học sammis.py V5.1.)
- numpy vectorized — CẤM vòng for Python trên từng element/voxel
  trong assembly, filter, update.
- Engine headless tuyệt đối: module engine KHÔNG import matplotlib/
  PyVista. Render là package tách rời chỉ đọc output.
- Dependencies khai trong requirements.txt — không cài ngoài danh sách.

## 3. Error-handling contract
- Spec sai → raise `SpecError(field, lý_do, gợi_ý_sửa)` — máy đọc được.
- Solver không hội tụ → raise `SolverError` kèm số vòng CG, residual.
- Không bao giờ trả kết quả "gần đúng" trong im lặng.

## 4. Interface contracts (ĐÃ LOCK — agent chỉ GỌI, không SỬA)
- (chưa có — sẽ lock dần sau mỗi tầng xanh, người ký)

## 5. Known issues
- Mount/encoding Windows từng gây bug ở sammis.py V5.1 — mọi CI phải có
  matrix Windows + Ubuntu từ ngày đầu.

## 6. Quyết định kiến trúc + LÝ DO
- **Problem-as-Data:** bài toán là spec.json, engine headless → agent (X2)
  tự viết bài và tự gọi engine được.
- **Benchmark-as-Truth:** đúng/sai do MBB beam (top88) và cantilever 3D
  (top3d) phán, sai số compliance ±5%.
- **2D trước, 3D sau:** 2D chứng minh BỘ TOÁN với chi phí rẻ; 3D giải lại
  bài toán trong không gian thật — KHÔNG extrude hình 2D lên 3D.
- **Compliance-based, không stress-based:** singularity vượt phạm vi Giai đoạn 1.
- **Ý tưởng mới → BACKLOG.md, không code** (rủi ro R4).
