# SPEC: stage2-t4-run-cli

> Tầng 2.4 — DoD-2.5: `python -m geophys run <spec.json>` chạy TRỌN pipeline
> không can thiệp tay. Mức: MEDIUM → câu 1–4. KHÔNG mở khóa protected.
> Ranh giới: CHỈ lệnh `run` (DoD-2.5). `validate`/`report` chuẩn hóa cho
> agent = Stage 3, vẫn CẤM (MANIFEST NOT BUILT giữ dòng đó).

## 1. Mục tiêu
Một lệnh: load spec v2 → optimize (checkpoint tự resume) → STL → render
PNG + viewer → report JSON + Markdown → exit code chuẩn. Mở khóa GP Studio
(BACKLOG) + nền CLI Stage 3.

## 2. Input
`python -m geophys run <spec> [--outdir DIR] [--method auto|direct|cg]
[--max-iter N] [--resume-from CKPT]`
Mặc định outdir: `runs/<tên-spec>/` (gitignore). --resume-from: copy
checkpoint có sẵn vào outdir (digest guard tự chặn nhầm bài).

## 3. Output (danh sách file ĐÓNG)
- `geophys/__main__.py` (entry mỏng, parse arg, exit code)
- `geophys/runner.py` (orchestrate; LỚP NGOÀI engine — được import
  render/export; engine core vẫn headless, guard test cũ canh)
- `tests/test_cli.py`
- `.gitignore` (SỬA: + runs/)
(spec này: `specs/stage2-t4-run-cli.md`)

## 4. Logic + exit code
0 = pipeline trọn + hội tụ + STL watertight · 1 = chạy xong nhưng FAIL
(không hội tụ / STL hỏng) · 2 = spec lỗi (SpecError — in đúng field/hint).
Outdir chứa: checkpoint.npz, optimize_log.json, <stem>.stl, <stem>_iso.png,
<stem>_viewer.html, report.json, report.md.
Resume-sau-hội-tụ: nếu resume mà không còn vòng nào chạy và change cuối
trong history < tol → công nhận hội tụ (không bắt chạy lại từ đầu).

## 5. Dependencies
Toàn bộ engine + render/export STABLE — CHỈ GỌI. Không dep mới.

## 6. Không được phép
Chạm 26 protected · lệnh validate/report (Stage 3) · GUI/server (BACKLOG).

## 7. Error handling
SpecError → stderr + exit 2 · file không tồn tại → SpecError path · lỗi
solver lan lên → in traceback + exit 1 · report LUÔN được ghi nếu đã
optimize xong (kể cả FAIL).

## 8. Acceptance
- Subprocess `python -m geophys run <spec nhỏ>` → exit 0; outdir đủ 7 file;
  report.json có compliance/volume/n_iter/converged/digest/vật liệu.
- Chạy LẦN HAI cùng lệnh → resume, exit 0 nhanh (resume-sau-hội-tụ OK).
- Spec hỏng → exit 2, stderr nêu field. --max-iter quá thấp → exit 1.
- report.md đọc được: bảng tóm tắt + đường dẫn file (nguyên liệu content
  — S2.1 #6 hợp đồng gốc).
- **DoD-2.5 chính thức:** NGƯỜI chạy nguyên văn
  `python -m geophys run examples/spec_brake_pedal.json`
  (thêm `--resume-from bench/brake_multi_checkpoint.npz` nếu muốn tái dùng
  25 phút đã chạy — digest tự xác thực cùng bài toán).

## 9. Ngoài phạm vi
validate/report/agent interface (Stage 3) · GP Studio (BACKLOG, mở sau
tầng này đóng) · spec 2D qua CLI (engine 2D là nền chứng minh, không phải
sản phẩm CLI).

---
## Phase 0 — câu 1–4 (MEDIUM)
1. **Output:** mục 3; pytest PASS; lệnh hợp đồng chạy được.
2. **Không chạm:** 26 protected + không sờ validate/report.
3. **Dependencies:** engine STABLE ✓.
4. **I/O:** CLI arg như mục 2; ra exit code + outdir; report JSON là
   contract dữ liệu cho tầng 2.5 và Stage 3 đọc lại.
