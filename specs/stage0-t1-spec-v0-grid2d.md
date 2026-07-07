# SPEC: stage0-t1-spec-v0-grid2d

> Task đầu tiên của Stage 0 (lõi 2D). Tương ứng hạng mục S0.1 #1–#2
> trong GEOMETRIC_PHYSICS_PLAN.txt. Mức rủi ro dự kiến: MEDIUM.

## 1. Mục tiêu
Loader cho `spec.json` schema v0 (bài toán 2D) + Grid Module 2D
(lưới phần tử vuông, ánh xạ element ↔ node, trường mật độ numpy).

## 2. Input
- File JSON schema v0, các trường bắt buộc:
  `nelx, nely` (int > 0), `volfrac` (0 < float < 1),
  `loads` (list: {node hoặc (x,y), fx, fy}), `supports` (list node/cạnh),
  `material` {E: float > 0, nu: 0 < float < 0.5},
  `simp` {p: mặc định 3.0, rmin: float > 0},
  `preserve` (list vùng ρ=1, được rỗng), `void` (list vùng ρ=0, được rỗng).

## 3. Output (danh sách file ĐÓNG)
- `geophys/__init__.py`
- `geophys/errors.py` (SpecError theo CONTEXT mục 3)
- `geophys/spec_loader.py`
- `geophys/grid2d.py`
- `tests/test_spec_loader.py`
- `tests/test_grid2d.py`
- `examples/spec_mbb_60x20.json`, `examples/spec_cantilever_40x20.json`,
  `examples/spec_preserve_void_20x20.json`
- `requirements.txt` (numpy, scipy, pytest — chỉ vậy)

## 4. Logic (từng bước, kể cả nhánh lỗi)
1. Đọc file UTF-8 → parse JSON; file không tồn tại / JSON hỏng → SpecError.
2. Validate từng trường theo mục 2; thiếu/sai kiểu/sai khoảng →
   SpecError(field, lý_do, gợi_ý) — nêu ĐÚNG TÊN TRƯỜNG.
3. Grid: node đánh số cột-trước (thứ tự top88 để so nghiệm chuẩn);
   element e ↔ 4 node (Q4); edof map dạng numpy array (nel, 8).
4. Trường mật độ khởi tạo = volfrac đồng nhất; áp mask preserve (ρ=1)
   và void (ρ=0); preserve ∩ void ≠ ∅ → SpecError.

## 5. Dependencies (+ lệnh verify từng cái)
- Python ≥ 3.11: `python --version`
- numpy: `python -c "import numpy; print(numpy.__version__)"`
- pytest: `python -m pytest --version`
- KHÔNG import scipy/matplotlib trong task này (FEA là task 2, render là task 5).

## 6. Không được phép
- Chạm file trong `.sammis/protected.list`.
- Import module NOT BUILT (fea2d, filter2d... — xem MANIFEST).
- Vòng for Python trên từng element khi build edof map.
- Thêm dependency ngoài requirements.txt.

## 7. Error handling (từng loại lỗi → hành động)
- File không tồn tại → SpecError("file", "không tìm thấy", đường dẫn đã thử).
- JSON hỏng → SpecError("json", vị trí lỗi từ parser, "kiểm tra dấu phẩy/ngoặc").
- Trường thiếu/sai → SpecError(tên_trường, giá_trị_nhận, khoảng_hợp_lệ).
- Không có bất kỳ except nuốt lỗi nào (anti-pattern #3).

## 8. Acceptance (lệnh chạy thật → kết quả kỳ vọng) — Tầng 1 Phụ lục A
- `python -m pytest tests/ -v` → PASS toàn bộ, trong đó tối thiểu:
  - 3 spec mẫu trong examples/ parse thành công.
  - Spec thiếu `nelx` → SpecError có chuỗi "nelx" trong thông báo.
  - Số node == (nelx+1)*(nely+1); số element == nelx*nely.
  - Round-trip element → 4 node → tọa độ → element: 100% khớp (test toàn lưới).
  - Trường mật độ sau mask: preserve toàn 1.0, void toàn 0.0,
    phần còn lại == volfrac.
- Chạy 2 lần liên tiếp ra kết quả giống hệt (deterministic).

## 9. Ngoài phạm vi
FEA, sensitivity, filter, OC, render, 3D, CLI — thuộc task/Stage sau.
Schema v1 (3D) — Stage 1.
