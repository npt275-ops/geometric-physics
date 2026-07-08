# SPEC: stage0-t5-render2d

> Tầng 0.5 — hạng mục S0.1 #8. Mức rủi ro: LOW → Phase 0 câu 1–2.
> Render là lớp TÁCH RỜI: engine không import nó; nó chỉ đọc output engine
> (nối qua callback của optimize — engine không biết bên kia là gì).

## 1. Mục tiêu
Xuất PNG trường mật độ + ghép GIF quá trình "ăn mòn" (DoD-0.8 —
deliverable build-in-public).

## 2. Input
rho (nelx, nely) ∈ [0,1] · quy ước hiển thị: đặc = đen, rỗng = trắng,
y hướng xuống (khớp lưới top88), phóng đại nearest ×8 mặc định.

## 3. Output (danh sách file ĐÓNG)
- `geophys/render2d.py`
- `tests/test_render2d.py`
- `media/mbb_evolution.gif` + `media/mbb_final.png` (bằng chứng DoD-0.8, sinh từ MBB benchmark)
- `requirements.txt` (SỬA: thêm matplotlib, pillow — nhóm render, engine không cần)
(spec này: `specs/stage0-t5-render2d.md`)

## 4. Logic
1. `render_field(rho, path, scale=8)` → PNG grayscale qua Pillow
   (nearest — giữ pixel sắc, không nội suy mờ).
2. `FrameRecorder(every=1, scale=8)` — callback cho optimize: chụp khung
   mỗi `every` vòng; `save_gif(path, fps=10)` ghép GIF (lặp vô hạn,
   giữ khung cuối 1s).
3. Path không ghi được → IOError lan lên, không nuốt.

## 5. Dependencies
matplotlib 3.10.9 ✓ (không bắt buộc trong module — Pillow đủ), pillow 12.2.0 ✓.

## 6. Không được phép
- Chạm 12 file protected. KHÔNG sửa optimize.py — nối bằng callback có sẵn.
- Module engine (spec_loader/grid2d/fea2d/sensitivity/filter2d/oc_update/
  optimize) tiếp tục KHÔNG import matplotlib/PIL — có test canh sys.modules.

## 7. Error handling
Path hỏng → IOError lan lên. rho sai shape/khoảng → ValueError.
save_gif khi chưa có khung nào → ValueError nêu rõ.

## 8. Acceptance
`python -m pytest tests/ -v` PASS, tối thiểu:
- PNG tồn tại, mở được bằng PIL, kích thước = (nelx·scale, nely·scale).
- Ngữ nghĩa pixel: ρ=1 → đen (<10), ρ=0 → trắng (>245); góc trên-trái
  của ảnh = element (0,0) — đúng hướng y-xuống.
- GIF: is_animated, n_frames khớp số vòng/every, mở được.
- Headless guard: import toàn bộ module engine → 'matplotlib' và 'PIL'
  KHÔNG có trong sys.modules; chỉ sau khi import render2d mới có PIL.
- DoD-0.8: media/mbb_evolution.gif sinh từ bài MBB 60×20 thật (94 khung),
  commit vào repo làm bằng chứng.

## 9. Ngoài phạm vi
Render 3D/PyVista, HTML viewer (Stage 1 Block F) · CI (0.6) · video editing.

---
## Phase 0 (LOW)
1. **Output:** như mục 3; lệnh `python -m pytest tests/ -v` PASS + 2 file media.
2. **Không chạm:** 12 file protected.
