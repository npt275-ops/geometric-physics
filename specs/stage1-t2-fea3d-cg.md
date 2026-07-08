# SPEC: stage1-t2-fea3d-cg

> Tầng 1.2 — TẦNG RỦI RO CAO NHẤT DỰ ÁN (Block B). Mức: HIGH → đủ 7 câu.
> Kế thừa sổ tay sự cố #1: solver 3D BẮT BUỘC có residual check —
> CG "giải ra rác" còn dễ hơn spsolve.

## 1. Mục tiêu
FEA 3D: KE H8 24×24, assembly sparse vectorized (COO precompute),
solver kép: spsolve (bài nhỏ — ground truth) + CG Jacobi preconditioner
(bài lớn), compliance + năng lượng element.

## 2. Input
Spec3D + Grid3D (STABLE — chỉ GỌI) · rho (nelx,nely,nelz) ∈ [0,1] ·
SIMP E(ρ) = Emin + ρ^p(E0−Emin), Emin = 1e-9·E0 (như 2D).

## 3. Output (danh sách file ĐÓNG)
- `geophys/fea3d.py`
- `tests/test_fea3d.py`
(spec này: `specs/stage1-t2-fea3d-cg.md`)

## 4. Logic
1. `ke_h8(E, nu)`: tích phân Gauss 2×2×2 trên voxel đơn vị, node order
   khớp Grid3D.element_nodes (4 đáy z → 4 đỉnh z+1), D đẳng hướng 6×6.
   Gauss 2 điểm là CHÍNH XÁC cho tích phân đa thức của H8 — kiểm bằng
   quadrature bậc cao hơn trong test.
2. `FEA3D(spec, grid)`: F (n_dof,) từ loads 3 thành phần; fixed dofs từ
   supports (x/y/z/all); COO index precompute MỘT lần.
3. `solve(rho, p, method="auto"|"direct"|"cg")`:
   - auto: n_dof ≤ 30_000 → direct; lớn hơn → cg.
   - direct: spsolve như 2D.
   - cg: scipy CG + Jacobi (1/diag) preconditioner, rtol 1e-10,
     maxiter 10·√n_dof·10 (trần cứng); không hội tụ → SolverError kèm
     số vòng + residual. Hỗ trợ warm start `x0` (nghiệm vòng trước).
   - CẢ HAI đường: residual check ‖Ku−f‖/‖f‖ ≤ 1e-6 → không đạt = SolverError.
4. `compliance(u)`, `element_energy(u, rho, p)` — einsum trên edof 24.

## 5. Dependencies (+ verify)
scipy.sparse.linalg.cg: `python -c "from scipy.sparse.linalg import cg"` ·
Tầng 1.1 STABLE (105 test xanh).

## 6. Không được phép
Chạm 16 file protected · vòng for voxel trong assembly/energy ·
matplotlib/PyVista trong engine · filter/OC/optimize 3D (tầng 1.3).

## 7. Error handling
CG không hội tụ → SolverError(số vòng, residual cuối) · K suy biến /
residual > 1e-6 → SolverError (cả direct lẫn cg) · rho/u sai shape → ValueError.

## 8. Acceptance — Tầng 2 Phụ lục A
- **KE hai bậc quadrature độc lập:** 2×2×2 vs 3×3×3 (viết trong test):
  max lệch < 1e-12 (đa thức — phải trùng đến máy).
- **KE tính chất:** đối xứng < 1e-14; đúng 6 rigid body mode (3 tịnh tiến
  + 3 xoay, eigenvalue ≈ 0), 18 mode dương.
- **Patch test 3D:** thanh kéo đều → ux(L) = σL/E sai < 1e-9; năng lượng
  element đồng nhất < 1e-9.
- **Dầm console 3D vs Timoshenko:** độ võng đầu dầm sai < 5%.
- **CG vs spsolve (điểm sống còn):** cùng bài ~1k element: ‖u_cg − u_direct‖
  / ‖u_direct‖ < 1e-6.
- **Warm start:** nghiệm với x0 = nghiệm đúng → hội tụ ≤ 5 vòng, kết quả khớp.
- **Thiếu ngàm → SolverError** (cả 2 method). **Deterministic** từng bit (direct).

## 9. Ngoài phạm vi
Filter 3D, sensitivity 3D, vòng lặp (1.3) · profiling 64×32×32 (1.4) · STL (1.5).

---
## Phase 0 — 7 câu (HIGH)
1. **Output:** 2 file + spec; `python -m pytest tests/ -v` PASS.
2. **Không chạm:** 16 file protected.
3. **Dependencies:** scipy.cg verify khi chạy; 105 test nền xanh ✓.
4. **I/O:** vào Spec3D+Grid3D+rho (nx,ny,nz); ra u (n_dof,) float64,
   compliance float > 0, energy (nx,ny,nz).
5. **STABLE liên quan:** grid3d (node order H8 LOCK — KE phải theo);
   spec3d (chỉ đọc); bài học residual từ fea2d (STABLE, không sửa nó).
6. **Lỗi từng bước:** CG treo → SolverError có số liệu; suy biến → residual
   check bắt; shape sai → ValueError; warm start shape sai → ValueError.
7. **Production?** Staging. Rollback: git revert; 16 file protected bất biến.
