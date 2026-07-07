# SPEC: stage0-t2-fea2d

> Tầng 0.2 — trái tim Stage 0. Hạng mục S0.1 #3 trong kế hoạch gốc.
> Mức rủi ro: HIGH → trả lời đủ 7 câu Phase 0 (ghi ở cuối spec).

## 1. Mục tiêu
FEA Solver 2D: phần tử Q4, lắp ráp ma trận độ cứng toàn cục sparse
(vectorized), áp điều kiện biên, giải KU = F, tính compliance và
mật độ năng lượng biến dạng từng element (nền cho Static Physics Test DoD-0.5).

## 2. Input
- `Spec` (từ spec_loader — STABLE, chỉ GỌI) + `Grid2D` (STABLE, chỉ GỌI).
- Trường mật độ `rho` shape (nelx, nely), giá trị [0, 1].
- Nội suy SIMP: E(ρ) = Emin + ρ^p (E0 − Emin), Emin = 1e-9·E0.

## 3. Output (danh sách file ĐÓNG)
- `geophys/fea2d.py`
- `tests/test_fea2d.py`
(spec này: `specs/stage0-t2-fea2d.md`)

## 4. Logic (từng bước, kể cả nhánh lỗi)
1. `ke_q4(E, nu)` → KE 8×8 giải tích theo top88 (plane stress, element 1×1,
   thứ tự dof khớp element_nodes của Grid2D: UL, UR, LR, LL).
2. `FEA2D(spec, grid)`: build F (ndof,) từ loads; fixed dofs từ supports;
   free = phần bù.
3. `assemble(rho, p)`: sK = outer(E(ρ), KE.ravel()) — thuần numpy,
   COO → CSR. Không vòng for trên element.
4. `solve(rho, p)`: spsolve trên hệ free dofs; U[fixed] = 0.
   Nghiệm chứa NaN/Inf (K suy biến — thiếu ngàm) → raise `SolverError`
   nêu rõ nghi vấn "thiếu ràng buộc rigid body".
5. `compliance(U)` = F·U; `element_energy(U, rho, p)` (nelx, nely)
   qua einsum trên edof_mat.

## 5. Dependencies (+ lệnh verify từng cái)
- numpy: `python -c "import numpy"` ✓ (2.2.6)
- scipy.sparse: `python -c "from scipy.sparse.linalg import spsolve"`
- geophys.spec_loader + grid2d: STABLE từ tầng 0.1, `python -m pytest tests/ -v` xanh.

## 6. Không được phép
- Chạm 7 file trong protected.list (gồm spec_loader.py, grid2d.py, errors.py).
- Import matplotlib/PyVista (engine headless — AST kiểm).
- Vòng for Python trên element trong assembly/energy.
- Filter, OC, vòng lặp tối ưu — thuộc tầng 0.3/0.4.

## 7. Error handling (từng loại lỗi → hành động)
- K suy biến / nghiệm NaN → `SolverError` (định nghĩa trong fea2d.py;
  đề xuất merge vào errors.py ở lần mở khóa protected kế — KHÔNG tự sửa errors.py).
- rho sai shape → `ValueError` nêu shape nhận được vs kỳ vọng.
- Không except nuốt lỗi.

## 8. Acceptance (lệnh chạy thật → kết quả kỳ vọng)
`python -m pytest tests/ -v` PASS toàn bộ, tối thiểu:
- **KE hai đường độc lập:** KE giải tích khớp KE tích phân Gauss 2×2
  (viết trong test, độc lập với module): max sai lệch < 1e-10.
- **KE tính chất:** đối xứng; đúng 3 rigid body mode (eigenvalue ≈ 0),
  5 mode dương.
- **Patch test:** tấm 4×4 kéo đều → năng lượng element đồng nhất
  (max lệch tương đối < 1e-9); chuyển vị mép phải = σL/E (sai < 1e-9).
- **Dầm console vs Timoshenko:** 80×10, tải phân bố mép phải,
  độ võng đầu dầm sai < 5% so với δ = PL³/3EI + PL/(κGA), κ = 5/6.
- **Static Physics (DoD-0.5, khối nguyên vẹn ρ=1):** cantilever 40×20,
  năng lượng 2 góc phải xa đường truyền lực < 20% mức trung bình toàn miền;
  năng lượng cực đại nằm tại element sát điểm đặt lực hoặc sát ngàm.
- **Thiếu ngàm → SolverError:** spec chỉ khóa 1 dof y → bắt được lỗi.
- **Deterministic:** 2 lần solve cùng rho → U giống hệt từng bit.

## 9. Ngoài phạm vi
Sensitivity, filter, OC, vòng lặp (0.3–0.4); render (0.5); 3D (Stage 1).

---
## Phase 0 — 7 câu (HIGH)
1. **Output:** 2 file code + spec này; lệnh `python -m pytest tests/ -v` → PASS.
2. **Không chạm:** 7 file protected.list.
3. **Dependencies:** numpy 2.2.6 ✓, scipy (verify khi chạy), tầng 0.1 STABLE ✓.
4. **I/O schema:** vào Spec + Grid2D + rho (nelx, nely) float64 [0,1];
   ra U (ndof,) float64, compliance float, energy (nelx, nely) float64.
5. **STABLE liên quan:** grid2d (quy ước node top88 — LOCK, fea2d phải theo);
   spec_loader (Spec bất biến — chỉ đọc).
6. **Lỗi từng bước:** JSON/spec sai → đã chặn ở tầng 0.1; K suy biến → SolverError;
   shape sai → ValueError; NaN lan truyền → chặn ngay sau spsolve.
7. **Production?** Không — staging. Rollback: `git revert` commit tầng 0.2,
   protected của 0.1 bất khả xâm phạm nên nền không thể vỡ.
