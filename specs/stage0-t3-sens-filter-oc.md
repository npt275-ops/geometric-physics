# SPEC: stage0-t3-sens-filter-oc

> Tầng 0.3 — bộ não của vòng lặp tối ưu. Hạng mục S0.1 #4–#7 kế hoạch gốc.
> Mức rủi ro: HIGH → đủ 7 câu Phase 0 (cuối spec).
> Phép kiểm quan trọng nhất dự án nằm ở đây: finite difference — bắt loại bug
> "gradient sai nhưng vẫn ra hình" nguy hiểm nhất của topology optimization.

## 1. Mục tiêu
Ba module: (a) Sensitivity ∂c/∂ρ compliance-based, (b) Sensitivity Filter
bán kính rmin chống checkerboard, (c) OC Update với bisection Lagrange
multiplier + move limit + tôn trọng preserve/void.

## 2. Input
- FEA2D + Grid2D + Spec (STABLE — chỉ GỌI), U từ solve(), rho (nelx, nely).
- Công thức: ∂c/∂ρₑ = −p·ρₑ^(p−1)·(E0−Emin)·(uₑᵀ KE uₑ). KHÔNG heuristic ứng suất.
- Filter kiểu top88: dcₙ = Σⱼ wⱼ ρⱼ dcⱼ / (max(ρₑ,1e-3)·Σⱼ wⱼ), w = max(0, rmin − dist).
  Cài bằng convolution (kernel cố định trên lưới đều) — không vòng for element.
- OC: xnew = clip(ρ·√(−dc/(dv·λ)), move limit 0.2, [0,1]); bisection λ;
  preserve ép 1, void ép 0 TRƯỚC khi tính thể tích; volume target = volfrac toàn cục.

## 3. Output (danh sách file ĐÓNG)
- `geophys/sensitivity.py`
- `geophys/filter2d.py`
- `geophys/oc_update.py`
- `tests/test_sensitivity.py`
- `tests/test_filter2d.py`
- `tests/test_oc_update.py`
(spec này: `specs/stage0-t3-sens-filter-oc.md`)

## 4. Logic (từng bước, kể cả nhánh lỗi)
1. sensitivity: validate shape rho (như fea2d) → einsum trên edof_mat → dc (nelx, nely) ≤ 0.
2. filter2d: class `SensitivityFilter(nelx, nely, rmin)` — precompute kernel
   + tổng trọng số biên (convolve ones) một lần; `apply(rho, dc)` → dc lọc.
   rmin ≤ 0 → ValueError (đã chặn từ spec_loader, chặn lại phòng gọi trực tiếp).
3. oc_update: kiểm khả thi trước — Σpreserve ≤ volfrac·nel ≤ nel − Σvoid,
   không thỏa → ValueError nêu con số cụ thể. Bisection đến (λ2−λ1)/(λ1+λ2) < 1e-6.
   dc dương (nhiễu số) → kẹp về 0 trong √. λ2 cạn (nghiệm sát biên) → ValueError.

## 5. Dependencies (+ lệnh verify)
- numpy ✓, scipy.signal.convolve2d: `python -c "from scipy.signal import convolve2d"`
- Tầng 0.1 + 0.2 STABLE: `python -m pytest tests/ -v` xanh (45 test hiện có).

## 6. Không được phép
- Chạm 8 file protected (gồm fea2d.py — sensitivity CHỈ GỌI fea.ke, fea.grid, fea.e0/e_min).
- Vòng for Python trên element trong module engine (test reference O(N²) trong TEST được phép).
- Vòng lặp tối ưu hoàn chỉnh — đó là tầng 0.4.
- matplotlib/PyVista trong engine.

## 7. Error handling
- rho/dc sai shape → ValueError nêu shape nhận vs kỳ vọng.
- Volume target bất khả thi với preserve/void → ValueError kèm 3 con số.
- Bisection không hội tụ sau 200 vòng → RuntimeError (không bao giờ trả kết quả gần đúng im lặng).

## 8. Acceptance (lệnh chạy thật → kết quả kỳ vọng) — Tầng 3 Phụ lục A + DoD-0.2/0.4
`python -m pytest tests/ -v` PASS toàn bộ, tối thiểu:
- **FD check (quan trọng nhất):** cantilever 8×6, ρ ngẫu nhiên seed 42 ∈ [0.3, 0.9],
  central difference h = 1e-6 trên 15 element ngẫu nhiên: sai lệch tương đối < 1%
  (kỳ vọng thực tế ~1e-6 vì compliance tự liên hợp).
- **dc ≤ 0 toàn miền** với mọi ρ ∈ (0, 1].
- **Filter vs reference O(N²):** lưới 7×5, rmin 2.1 — convolution khớp cài đặt
  tường minh 2 vòng for (viết trong test): max lệch < 1e-12.
- **Filter bảo toàn trường hằng:** dc = const, ρ = const → lọc xong vẫn = const (±1e-12).
- **Filter đập checkerboard:** dc xen kẽ ±1, rmin = 1.5 → max|dc lọc| < 0.5·max|dc| (DoD-0.2 gốc).
- **OC volume:** sau update |mean(xnew) − volfrac| < 1e-3.
- **OC move limit:** |xnew − ρ| ≤ 0.2 + 1e-12 trên vùng tự do.
- **OC preserve/void:** giữ nguyên 1/0 tuyệt đối (DoD-0.4).
- **OC đơn điệu:** ρ đều + dc phân biệt → thứ hạng xnew khớp thứ hạng (−dc) trên vùng chưa chạm biên/move.
- **OC bất khả thi → ValueError**; **deterministic** cho cả 3 module.

## 9. Ngoài phạm vi
Vòng lặp hội tụ + benchmark MBB (0.4); render (0.5); density filter (biến thể
khác — BACKLOG nếu cần); 3D (Stage 1).

---
## Phase 0 — 7 câu (HIGH)
1. **Output:** 6 file trên + spec; lệnh `python -m pytest tests/ -v` → PASS.
2. **Không chạm:** 8 file protected.list hiện hành.
3. **Dependencies:** numpy 2.2.6 ✓, scipy 1.15.3 ✓ (convolve2d verify khi chạy), 45 test nền xanh ✓.
4. **I/O schema:** dc (nelx, nely) float64 ≤ 0; filter trả cùng shape;
   oc_update trả xnew (nelx, nely) ∈ [0,1] thỏa volume.
5. **STABLE liên quan:** fea2d.ke/e0/e_min/grid — chỉ đọc; edof convention top88 LOCK.
6. **Lỗi từng bước:** shape sai → ValueError; bất khả thi → ValueError kèm số;
   bisection treo → RuntimeError sau 200 vòng; dc dương nhiễu → kẹp 0 có chủ đích (ghi docstring).
7. **Production?** Không — staging. Rollback: git revert commit tầng; nền 0.1/0.2 protected.
