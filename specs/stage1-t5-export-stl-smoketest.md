# SPEC: stage1-t5-export-stl-smoketest

> Tầng 1.5 — Block E (kéo từ Stage 2 lên theo v1.1). Mức: MEDIUM → câu 1–4.
> Cổng NGƯỜI: bước FreeCAD là reality verification — agent chỉ soạn hướng dẫn,
> NGƯỜI thao tác + chụp bằng chứng. DoD-1.7 chỉ đóng khi có bằng chứng đó.

## 1. Mục tiêu
Trường mật độ 3D → STL kín (watertight): marching cubes (isosurface 0.5,
PAD biên 0 chống mesh hở — đối sách S1-R3) → làm mượt Taubin nhẹ (biến thể
Laplacian giữ thể tích) → kiểm tự động bằng trimesh → file STL + report.
Deliverable: STL cantilever 60×20×4 (kết quả tầng 1.3) + hướng dẫn FreeCAD.

## 2. Input
rho (nelx,nely,nelz) ∈ [0,1] · iso mặc định 0.5 · smooth_iters mặc định 10.

## 3. Output (danh sách file ĐÓNG)
- `geophys/export_stl.py`
- `tests/test_export_stl.py`
- `media/cantilever3d_60x20x4.stl` (deliverable, sinh từ kết quả benchmark 1.3)
- `HUONG_DAN_FREECAD.md` (từng bước cho FreeCAD 1.1.x, checklist bằng chứng)
- `requirements.txt` (SỬA: + scikit-image, trimesh)

## 4. Logic
1. Kiểm rho hợp lệ; (rho > iso) rỗng → ValueError "không có vật chất".
2. Pad 1 lớp 0 quanh khối → marching_cubes(level=iso) → Trimesh.
3. Lọc mảnh vụn: bỏ component thể tích < 1% tổng (ghi số lượng vào report
   — minh bạch, không lặng lẽ); còn > 1 component lớn → report ghi rõ.
4. Taubin smoothing (λ=0.5, ν=−0.53) — giữ thể tích tốt hơn Laplacian thuần.
5. Export STL binary + report dict: watertight, n_components (sau lọc),
   volume_stl, volume_voxel, lệch %, n_faces.

## 5. Dependencies (+ verify)
scikit-image (marching_cubes), trimesh: `python -c "import skimage, trimesh"`.

## 6. Không được phép
Chạm 21 file protected · engine import module này (một chiều: export đọc rho)
· tự tuyên bố DoD-1.7 đạt khi chưa có bằng chứng NGƯỜI.

## 7. Error handling
rho rỗng vật chất / iso ∉ (0,1) / shape sai → ValueError ·
mesh không watertight sau pipeline → ExportError nêu số liệu (không trả file rác).

## 8. Acceptance
- Khối hộp đặc 8×4×4 → STL: watertight, 1 component, volume lệch < 5%
  so với 128 (giải tích), bounding box đúng.
- Khối cầu (rasterize Grid3D) → volume lệch < 3% so 4/3πr³ (đo 0.88%).
- Kết quả optimize3d thật (12×6×4) → watertight, 1 component, volume vs
  voxel < 10% (biên xám SIMP — đo 6.23% trên bài 60×20×4).
- rho toàn 0 → ValueError; iso=1.2 → ValueError; deterministic (2 lần
  export → bytes giống hệt).
- **DoD-1.7 (NGƯỜI):** STL cantilever mở trong FreeCAD 1.1 → mesh Gmsh
  → ngàm mặt x0 + lực đầu tự do → CalculiX chạy hết không lỗi → Von Mises
  tập trung gần ngàm → screenshot + file .FCStd lưu bench/ → commit.

## 9. Ngoài phạm vi
Von Mises < giới hạn chảy (DoD-2.3, Stage 2) · materials.json (Stage 2) ·
render/viewer (1.6).

---
## Phase 0 — câu 1–4 (MEDIUM)
1. **Output:** mục 3; pytest PASS + STL deliverable + hướng dẫn.
2. **Không chạm:** 21 file protected.
3. **Dependencies:** cài + verify khi chạy; 134 test nền xanh.
4. **I/O:** vào rho ndarray; ra (Path STL, report dict) — report là dữ liệu
   máy-đọc-được cho Stage 2/3 dùng lại.
