# SPEC: stage1-t6-render-viewer

> Tầng 1.6 — Block F, OPTIONAL (DoD-1.8 không chặn cửa ải Stage 1).
> Mức: LOW → Phase 0 câu 1–2. Lớp render TÁCH RỜI — engine không biết.

## 1. Mục tiêu
(a) Ảnh isosurface tĩnh (PNG) tại các mốc vòng lặp — matplotlib trisurf
trên mesh marching-cubes (quyết định: KHÔNG thêm PyVista/VTK — dep nặng,
kế hoạch gốc cho phép lựa chọn matplotlib). (b) HTML viewer TỰ CHỨA
100% offline: renderer canvas thuần JS (không CDN, không three.js) —
xoay (kéo chuột), zoom (lăn chuột), slider tiến hóa qua các mốc.

## 2. Input
rho (nx,ny,nz) hoặc chuỗi snapshot rho từ callback optimize3d ·
iso 0.5 · tái dùng rho_to_mesh (export_stl STABLE — chỉ GỌI).

## 3. Output (danh sách file ĐÓNG)
- `geophys/render3d.py` (render_isosurface + SnapshotRecorder3D.to_html)
- `tests/test_render3d.py`
- `media/cantilever3d_iso.png` + `media/cantilever3d_viewer.html`
  (deliverable từ kết quả benchmark 1.3)

## 4. Logic
SnapshotRecorder3D(every) làm callback optimize3d → giữ bản sao rho các mốc;
to_html(path): mỗi mốc → mesh (smooth nhẹ) → JSON {v,f} nhúng thẳng vào
HTML template + JS renderer (flat shading, painter's sort, quay quanh tâm).
PNG: trisurf, trục đúng tỷ lệ khối, y-down xử lý để nhìn tự nhiên.
Lỗi IO → lan lên; rho sai → ValueError từ rho_to_mesh.

## 5. Dependencies
matplotlib ✓, trimesh/skimage ✓ (qua export_stl). KHÔNG dep mới.

## 6. Không được phép
Chạm 22 file protected · engine import render3d (headless guard đang canh
matplotlib) · CDN/script ngoài trong HTML (phải mở offline).

## 7. Error handling
to_html khi 0 snapshot → ValueError · path hỏng → IOError lan lên.

## 8. Acceptance — DoD-1.8 (optional)
- PNG: file mở được (PIL), kích thước > 10KB, đúng số mốc yêu cầu (≥5 khi
  chạy bài thật).
- HTML: tự chứa (không http://, https:// trong src), chứa đúng N mesh JSON
  khớp số snapshot, có canvas + slider + handler wheel/drag.
- Chạy trên optimize3d thật (bài nhỏ): recorder bắt đúng mốc every=k.
- Engine headless guard cũ vẫn xanh (render3d không lọt vào engine).

## 9. Ngoài phạm vi
Viewer nâng cao (so sánh 2 run — BACKLOG) · GP Studio (BACKLOG, sau DoD-2.5)
· video/animation tự động.

---
## Phase 0 (LOW)
1. **Output:** mục 3; pytest PASS + 2 deliverable media/.
2. **Không chạm:** 22 file protected.
