# SPEC: stage1-t3-optimize3d-benchmark

> Tầng 1.3 — "khoảnh khắc MBB" của Stage 1 (Block C). Mức: HIGH → đủ 7 câu.

## 1. Mục tiêu
Port bộ não tối ưu lên 3D: sensitivity ∂c/∂ρ (24 dof), filter 3D
(kernel cầu rmin), vòng lặp hoàn chỉnh. Benchmark cantilever 60×20×4
đối chứng bản tham chiếu monolithic độc lập theo thuật toán top3d công bố
(Liu & Tovar 2014). DoD-1.1 + DoD-1.5 + DoD-1.6.

## 2. Input
Spec3D/Grid3D/FEA3D (STABLE — chỉ GỌI) · **TÁI DÙNG `oc_update` STABLE
nguyên trạng** — hàm element-wise, không phụ thuộc số chiều (bằng chứng:
test 3D gọi trực tiếp). Công thức sensitivity/filter y hệt 2D, đổi chiều.

## 3. Output (danh sách file ĐÓNG)
- `geophys/sensitivity3d.py`
- `geophys/filter3d.py` (scipy.ndimage.convolve, kernel 3D tiền tính)
- `geophys/optimize3d.py` (vòng lặp; warm start CG bằng nghiệm vòng trước;
  tái dùng dataclass OptimizeResult từ optimize — STABLE, chỉ import)
- `tests/test_optimize3d.py`
(spec này: `specs/stage1-t3-optimize3d-benchmark.md`)

## 4. Logic
Như optimize 2D: solve → dc → filter → oc_update → change < tol (0.01),
max 200 vòng; history + log JSON + callback; converged tường minh.
Lỗi tầng dưới lan nguyên vẹn. Bản tham chiếu benchmark viết TRONG TEST:
monolithic, tự lắp ráp, tự filter (vòng for tường minh), tự OC — độc lập
mọi module trừ công thức KE đã kiểm 2-đường ở tầng 1.2.

## 5. Dependencies (+ verify)
scipy.ndimage.convolve: `python -c "from scipy.ndimage import convolve"` ·
119 test nền xanh.

## 6. Không được phép
Chạm 17 file protected (oc_update DÙNG, không SỬA) · vòng for voxel trong
module · checkpoint/resume (1.4) · STL (1.5).

## 7. Error handling
Shape sai → ValueError · volume bất khả thi → ValueError (oc_update lo) ·
CG treo → SolverError lan lên · không hội tụ → converged=False tường minh.

## 8. Acceptance — Tầng 3 Phụ lục A + DoD-1.1/1.5/1.6
- **FD check 3D:** cantilever 6×4×4, ρ ngẫu nhiên seed 42, 12 element:
  sai < 1% (kỳ vọng ~1e-6).
- **Filter 3D vs reference O(N²) tường minh:** lưới 6×5×4, rmin 1.9: < 1e-12;
  trường hằng bảo toàn; checkerboard 3D bị đập < 0.5.
- **DoD-1.1:** cantilever 60×20×4 (spec example, volfrac 0.3, rmin 1.5):
  compliance GP vs reference monolithic: lệch < 5%.
- **DoD-1.5:** bài đối xứng gương theo z → ‖ρ − mirror_z(ρ)‖ / ‖ρ‖ < 1%.
- **DoD-1.6:** toàn bộ test 2D cũ vẫn xanh (chạy chung suite).
- Hội tụ < 200 vòng, đơn điệu (dao động < 2%), volume ±1%, preserve/void
  giữ nguyên từng vòng (watchdog), deterministic (bài nhỏ, 2 lần trùng bit).

## 9. Ngoài phạm vi
Hiệu năng 64×32×32 + checkpoint (1.4) · STL/FreeCAD (1.5) · render (1.6).

---
## Phase 0 — 7 câu (HIGH)
1. **Output:** 4 file + spec; `python -m pytest tests/ -v` PASS (chạy nền vì suite dài).
2. **Không chạm:** 17 file protected.
3. **Dependencies:** ndimage verify khi chạy; 119 test xanh ✓.
4. **I/O:** vào Spec3D; ra OptimizeResult(rho 3D, compliance, n_iter, converged, history).
5. **STABLE liên quan:** fea3d (solve method/x0 — LOCK), oc_update (chỉ gọi),
   optimize.OptimizeResult (chỉ import).
6. **Lỗi:** như mục 7; benchmark không hội tụ → test FAIL rõ ràng, không nới tol.
7. **Production?** Staging. Rollback: git revert; 17 file protected bất biến.
