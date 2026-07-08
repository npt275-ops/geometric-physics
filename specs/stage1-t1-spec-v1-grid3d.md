# SPEC: stage1-t1-spec-v1-grid3d

> Tầng 1.1 Stage 1 — nền dữ liệu 3D. Block A trong STAGE1_EXECUTION_PLAN.
> Mức rủi ro: MEDIUM → Phase 0 câu 1–4 (cuối spec).

## 1. Mục tiêu
Schema spec.json v1 (3D) + Grid Module 3D: voxel H8, ánh xạ element ↔ node,
vùng bảo tồn/cấm bằng HÌNH KHỐI NGUYÊN THỦY (hộp, trụ, cầu) thay vì liệt kê voxel.

## 2. Input — schema v1
Trường bắt buộc: `nelx, nely, nelz` (int ≥ 1), `volfrac`, `loads`
(list {x,y,z hoặc node; fx, fy, fz}), `supports` (list {face: x0|x1|y0|y1|z0|z1
hoặc node/x,y,z; dof: x|y|z|all}), `material` {E, nu}, `simp` {p, rmin},
`preserve`/`void` (list hình khối):
- box: {type: "box", x0,y0,z0, x1,y1,z1} — tọa độ ELEMENT, biên bao gồm, PHẢI trong lưới.
- sphere: {type: "sphere", cx,cy,cz, r} — tâm phải trong lưới; mask cắt theo biên lưới.
- cylinder: {type: "cylinder", axis: x|y|z, + 2 tọa độ tâm vuông góc trục
  (vd axis z → cx,cy), r, + khoảng dọc trục (vd axis z → z0,z1)}.
Rasterize tại TÂM element (ex+0.5, ey+0.5, ez+0.5).

## 3. Output (danh sách file ĐÓNG)
- `geophys/spec3d.py` (Spec3D + load_spec3d — TÁI DÙNG validator private của
  spec_loader qua import, KHÔNG sửa spec_loader)
- `geophys/grid3d.py` (Grid3D: node/element mapping, edof (nel,24), mask, rho)
- `tests/test_spec3d.py`, `tests/test_grid3d.py`
- `examples/spec3d_cantilever_60x20x4.json`, `examples/spec3d_primitives_20.json`

## 4. Logic + quy ước (LOCK từ đây)
- node_id(x,y,z) = z·(nelx+1)(nely+1) + x·(nely+1) + y — lát z=0 trùng quy ước 2D.
- element_id = ravel C-order của (ex,ey,ez) trên shape (nelx,nely,nelz).
- H8 node order: [(x,y,z),(x+1,y,z),(x+1,y+1,z),(x,y+1,z)] rồi 4 node lặp lại
  ở z+1. dof node n = [3n, 3n+1, 3n+2].
- rho shape (nelx,nely,nelz); preserve→1, void→0; preserve ∩ void (sau
  rasterize) ≠ ∅ → SpecError.
- Nhánh lỗi: thiếu trường → SpecError đúng tên; node/box ngoài lưới → SpecError;
  primitive type lạ → SpecError; lực 0 → SpecError; không support → SpecError.

## 5. Dependencies (+ verify)
numpy ✓ · spec_loader/errors STABLE (chỉ gọi) · 79 test nền xanh.

## 6. Không được phép
Chạm 14 file protected · FEA/filter/OC 3D (tầng 1.2–1.3) · vòng for voxel
trong rasterize/edof (vòng for trên REGION được phép).

## 7. Error handling
Như mục 4; shape/khoảng sai → SpecError(field, reason, hint) máy đọc được.

## 8. Acceptance — Tầng 1 Phụ lục A
`python -m pytest tests/ -v` PASS (79 test cũ + mới), tối thiểu:
- 2 spec 3D mẫu parse OK; thiếu `nelz` → SpecError nêu "nelz".
- Số node = (nelx+1)(nely+1)(nelz+1); số element = nelx·nely·nelz; edof (nel,24).
- Round-trip node & element toàn lưới: 100% (vectorized).
- 8 node H8 đúng vị trí hình học toàn lưới.
- Rasterize: box đúng TỪNG VOXEL (đếm chính xác); sphere & cylinder sai
  < 2% so thể tích giải tích (lưới đủ mịn, hình nằm trọn trong lưới).
- preserve ∩ void → SpecError; rho init đúng volfrac ngoài vùng.
- Schema v0 2D không vỡ (toàn bộ test cũ xanh).
- Deterministic: load + Grid3D 2 lần giống hệt.

## 9. Ngoài phạm vi
FEA 3D, KE H8 (1.2) · optimize 3D (1.3) · checkpoint (1.4) · STL (1.5).

---
## Phase 0 — câu 1–4 (MEDIUM)
1. **Output:** 6 file mục 3; lệnh `python -m pytest tests/ -v` PASS.
2. **Không chạm:** 14 file protected.list.
3. **Dependencies:** numpy 2.2.6 ✓; spec_loader STABLE import được ✓ (79 test).
4. **I/O schema:** vào JSON v1 như mục 2; ra Spec3D bất biến + Grid3D
   (edof int64 (nel,24), rho float64 (nelx,nely,nelz), mask bool cùng shape).
