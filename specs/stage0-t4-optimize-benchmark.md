# SPEC: stage0-t4-optimize-benchmark

> Tầng 0.4 — cửa ải quyết định Stage 0: nối 4 mảnh đã kiểm chứng thành vòng
> lặp hoàn chỉnh, chạy MBB beam đối chứng chuẩn top88. Mức rủi ro: HIGH.

## 1. Mục tiêu
Vòng lặp tối ưu: solve → dc → filter → OC → kiểm hội tụ, lặp đến khi
max|Δρ| < 0.01 hoặc chạm 200 vòng. Benchmark DoD-0.1 + DoD-0.3/0.4/0.6.

## 2. Input
Spec (mọi tham số từ spec.json: volfrac, p, rmin, preserve, void).
Tùy chọn: max_iter=200, tol=0.01, move=0.2, log_path (ghi history JSON),
callback(iter, rho, c) — móc nối cho render tầng 0.5 mà engine không import gì.

## 3. Output (danh sách file ĐÓNG)
- `geophys/optimize.py`
- `tests/test_optimize.py`
(spec này: `specs/stage0-t4-optimize-benchmark.md`)

## 4. Logic
1. Grid2D(spec) → ρ₀ (volfrac + preserve/void đã áp từ tầng 0.1).
2. Mỗi vòng: U = solve(ρ) → c = F·U → dc = dc_drho → dc lọc = filter.apply
   → ρ⁺ = oc_update. change = max|ρ⁺−ρ|.
3. History: compliance, change, volume mỗi vòng (list trong RAM;
   log_path → ghi JSON mỗi 10 vòng + cuối).
4. Trả OptimizeResult(rho, compliance, n_iter, converged, history)
   — converged=False là kết quả TƯỜNG MINH, không nuốt.
5. SolverError/ValueError từ tầng dưới → lan lên nguyên vẹn, không bọc nuốt.

## 5. Dependencies (+ verify)
numpy/scipy ✓; 4 module STABLE tầng 0.1–0.3 (66 test xanh) — CHỈ GỌI.

## 6. Không được phép
Chạm 11 file protected · matplotlib/PyVista trong engine · vòng for element
· sửa thuật toán các tầng dưới (phát hiện sai → DỪNG, báo, không vá tại 0.4).

## 7. Error handling
Không hội tụ sau max_iter → converged=False + history đầy đủ (caller quyết).
log_path không ghi được → IOError lan lên (không nuốt).

## 8. Acceptance — DoD-0.1, 0.3, 0.4, 0.6
`python -m pytest tests/ -v` PASS, tối thiểu:
- **DoD-0.1 (TỐI THƯỢNG Stage 0):** MBB 60×20, volfrac 0.5, p=3, rmin=1.5 —
  compliance cuối khớp bản PORT TOP88 TRUNG THỰC viết độc lập trong test
  (monolithic, đúng từng công thức bài báo Andreassen 2011): sai lệch < 5%
  (kỳ vọng thực tế ≪1% vì cùng thuật toán, khác kiến trúc code).
- **DoD-0.2:** detector 2×2 xen kẽ đặc/rỗng trên kết quả MBB nhị phân hóa: 0 pattern.
- **DoD-0.3:** converged=True, n_iter < 200; compliance giảm đơn điệu
  (cho phép dao động < 2% giữa 2 vòng liên tiếp).
- **DoD-0.4:** bài preserve_void_20x20 — preserve ρ=1, void ρ=0 tuyệt đối
  ở KẾT QUẢ CUỐI và MỌI vòng (kiểm qua callback); volume cuối ±1% volfrac.
- **DoD-0.6:** cantilever 20×10 chạy 2 lần → ρ giống hệt từng bit.
- Cấu trúc MBB có giàn chéo: thanh biên trên/dưới đặc + ít nhất một
  đường chéo vật liệu nối 2 biên (kiểm bằng mật độ trên các băng chéo).

## 9. Ngoài phạm vi
Render/GIF (0.5) · CI (0.6) · checkpoint file resume (Stage 1) · CLI (Stage 3).

---
## Phase 0 — 7 câu (HIGH)
1. **Output:** 2 file + spec; `python -m pytest tests/ -v` PASS.
2. **Không chạm:** 11 file protected.
3. **Dependencies:** 66 test nền xanh ✓, numpy/scipy ✓.
4. **I/O:** vào Spec; ra OptimizeResult(rho (nelx,nely) ∈[0,1], compliance>0,
   n_iter≤200, converged bool, history dict[list]).
5. **STABLE liên quan:** cả 4 module dưới — interface lock, chỉ gọi.
6. **Lỗi:** không hội tụ → cờ tường minh; lỗi tầng dưới lan nguyên vẹn;
   log IO lỗi → lan lên.
7. **Production?** Staging. Rollback: git revert; 11 file protected bất biến.
