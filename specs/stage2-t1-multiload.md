# SPEC: stage2-t1-multiload

> Tầng 2.1 Stage 2 — nâng cấp quyết định của hợp đồng gốc: "cấu trúc tối ưu
> cho MỘT hướng lực là cấu trúc mỏng manh nhất với mọi hướng còn lại".
> Mức: HIGH → đủ 7 câu Phase 0.
>
> **ĐỀ XUẤT MỞ KHÓA PROTECTED (điều 5 AGENT_RULES):** cần sửa 3 file STABLE
> `geophys/spec3d.py` (schema v2), `geophys/fea3d.py` (đa vector lực),
> `geophys/optimize3d.py` (tổng compliance trọng số). Bảo hiểm hồi quy:
> GOLDEN VALUES chụp bằng code hiện tại TRƯỚC khi sửa (12/07):
>   G1 direct 12×6×4: 26 vòng, c=28.964919725332997,
>      rho sha256=e9167fb4797180f62b0745e3d3ca04e5cf2810b0857267fcaad288e64a57b23d
>   G2 CG+preserve/void 10×10×6: 27 vòng, c=10.079410389351352,
>      rho sha256=9ff77ed18f7b9ed821128a65b31bde5674c81416aaa938e4548c8dee438e2330
> Code mới chạy spec cũ PHẢI tái tạo đúng hash — không đạt = tầng FAIL.

## 1. Mục tiêu
spec.json v2 nhận `load_cases` (danh sách case kèm trọng số). Hàm mục tiêu
c = Σ wᵢ·cᵢ; gradient dc = Σ wᵢ·dcᵢ. Warm start CG riêng từng case.

## 2. Input — schema v2
- HOẶC `"loads"` (v1, giữ nguyên — nội bộ thành 1 case weight 1.0),
- HOẶC `"load_cases": [{"weight": w>0, "loads": [...]}, ...]` (≥1 case).
- Cả hai cùng lúc → SpecError "chọn một"; không cái nào → SpecError.
- Mỗi case validate như loads v1 (lực 0 bị chặn, node trong lưới).

## 3. Output (danh sách file ĐÓNG)
- `geophys/spec3d.py` (SỬA — thêm parse load_cases, field mới trong Spec3D)
- `geophys/fea3d.py` (SỬA — self.forces list; solve(..., force=None);
  self.force = forces[0] để đường đơn-case GIỮ NGUYÊN TỪNG BIT)
- `geophys/optimize3d.py` (SỬA — vòng case: cᵢ, dcᵢ → tổng trọng số;
  u_prev thành danh sách theo case; checkpoint lưu mảng (ncase, ndof) —
  checkpoint.py KHÔNG sửa, format npz nuốt được mảng 2D)
- `tests/test_multiload.py`
(spec này: `specs/stage2-t1-multiload.md`)

## 4. Logic
1. Parse: load_cases → tuple((w, tuple(Load3D)), …); spec.loads = case đầu
   (tương thích code đọc cũ).
2. FEA3D: forces[i] từ case i. solve nhận force tùy chọn (mặc định
   forces[0] ≡ hành vi cũ). compliance(u, force=None) tương tự.
3. optimize3d mỗi vòng: với từng case i: uᵢ = solve(ρ, force=fᵢ, x0=u_prevᵢ)
   → cᵢ = fᵢ·uᵢ → dcᵢ; c = Σwᵢcᵢ; dc = Σwᵢdcᵢ → filter → OC (không đổi).
   history thêm "c_cases"; cg_iters = tổng các case.
4. Checkpoint: u_prev lưu np.stack(u_prevs); resume chấp nhận cả mảng 1D cũ
   (1 case) lẫn 2D mới — digest spec vẫn canh nhầm bài.
5. Nhánh lỗi: weight ≤ 0 → SpecError; load_cases rỗng → SpecError;
   lỗi tầng dưới lan nguyên vẹn.

## 5. Dependencies (+ verify)
Không dep mới. 146 test nền + golden values ở trên.

## 6. Không được phép
- Đổi thuật toán OC/filter/sensitivity (chỉ GỌI).
- Đổi hành vi khi spec chỉ có "loads" — golden hash là trọng tài.
- Chạm 21 file protected còn lại.

## 7. Error handling
Như mục 4.5 · force shape sai trong solve → ValueError · x0 list lệch số
case → ValueError.

## 8. Acceptance
`python -m pytest tests/ -v` PASS (trừ benchmark CI), tối thiểu:
- **HỒI QUY GOLDEN (cửa sinh tử):** chạy lại G1, G2 bằng code mới —
  n_iter, compliance (repr đầy đủ), sha256(rho) TRÙNG KHỚP hằng số ở trên.
- **Tương đương v1↔v2:** cùng bài viết kiểu "loads" vs "load_cases" 1 case
  w=1.0 → rho giống hệt TỪNG BIT.
- **FD check multi:** 2 case (w=0.7/0.3), c = Σwᵢcᵢ đối chiếu central
  difference trên 10 voxel: sai < 1% (kỳ vọng ~1e-6).
- **Khác biệt định lượng:** bài 2 case (lực −y và lực ngang z) vs bài chỉ
  case 1: ‖ρ_multi − ρ_single‖/‖ρ_single‖ > 5% — multi-load THẬT SỰ đổi
  cấu trúc.
- **Checkpoint multi-case:** ngắt giữa chừng → resume → giống hệt từng bit.
- **Nhánh lỗi:** weight=0, weight=-1, load_cases=[], có cả loads lẫn
  load_cases, thiếu cả hai → SpecError đúng tên trường.

## 9. Ngoài phạm vi
materials.json/đơn vị thật (2.2) · bàn đạp phanh (2.3) · CLI (2.4) ·
min-max compliance (biến thể robust — BACKLOG nếu cần).

---
## Phase 0 — 7 câu (HIGH)
1. **Output:** mục 3; pytest PASS + golden hash trùng.
2. **Không chạm:** 21 file protected còn lại (3 file mở khóa có nghi thức).
3. **Dependencies:** không dep mới; suite 146 + golden đã chụp ✓.
4. **I/O:** Spec3D thêm field load_cases; OptimizeResult không đổi hình dạng
   (history thêm khóa mới — cộng, không sửa).
5. **STABLE liên quan:** oc_update/filter3d/sensitivity3d/checkpoint — CHỈ GỌI.
6. **Lỗi từng bước:** mục 7; golden lệch 1 bit = dừng, tìm nguyên nhân,
   không "chấp nhận xấp xỉ".
7. **Production?** Staging. Rollback: git revert 3 file; golden test là chuông báo.
