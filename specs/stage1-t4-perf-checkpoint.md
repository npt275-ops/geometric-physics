# SPEC: stage1-t4-perf-checkpoint

> Tầng 1.4 — Block D. Mức: MEDIUM → Phase 0 câu 1–4.
> **ĐỀ XUẤT MỞ KHÓA PROTECTED (điều 5 AGENT_RULES — dừng và đề xuất):**
> checkpoint/profiling phải nằm TRONG vòng lặp → cần sửa `geophys/optimize3d.py`
> (đóng ở 1.3). Thay đổi CHỈ THÊM tham số mặc định tắt (checkpoint_path,
> checkpoint_every, resume) + đo thời gian/RAM vào history — không đổi
> thuật toán, không đổi kết quả khi tham số mới không dùng (có test chứng minh).
> Người vận hành duyệt spec này = ký lệnh mở khóa.

## 1. Mục tiêu
(a) Checkpoint/Resume: ngắt bài chạy dài, chạy tiếp, kết quả GIỐNG HỆT
chạy liền mạch (DoD-1.4). (b) Profiling từng khâu + peak RAM ghi log
(nền cho DoD-1.2/1.3). (c) Bộ đo cho NGƯỜI chạy trên laptop: bài 64×32×32.

## 2. Input
Spec3D · checkpoint .npz chứa: digest spec (sha256, chống resume nhầm bài),
rho, u_prev (warm start CG — để resume CG cũng giống hệt), n_iter, history JSON.

## 3. Output (danh sách file ĐÓNG)
- `geophys/checkpoint.py` (save/load/digest)
- `geophys/optimize3d.py` (SỬA — theo đề xuất trên, mở khóa + khóa lại)
- `tests/test_checkpoint.py`
- `examples/spec3d_bench_64x32x32.json`
- `scripts/benchmark_laptop.py` + `RUN_BENCHMARK.bat` (người vận hành double-click)
- `requirements.txt` (SỬA: thêm psutil — đo RSS đa nền tảng)

## 4. Logic
optimize3d thêm: resume=True → nạp checkpoint (digest lệch → ValueError),
tiếp vòng start+1; lưu mỗi `checkpoint_every` vòng + khi kết thúc.
History thêm: t_solve, t_grad_filter, t_oc (giây/vòng), rss_mb.
Vì mỗi vòng chỉ phụ thuộc (rho, u_prev) và cả hai được lưu → resume
tái lập đúng quỹ đạo, cả direct lẫn CG.

## 5. Dependencies
psutil: `python -c "import psutil"` (thiếu → rss_mb = -1, không chặn engine).

## 6. Không được phép
Đổi công thức/thuật toán trong optimize3d · chạm 19 file protected còn lại ·
tự ý coi DoD-1.2/1.3 là đạt bằng số sandbox — HAI DoD NÀY CHỈ ĐÓNG BẰNG
SỐ ĐO TRÊN LAPTOP CỦA NGƯỜI VẬN HÀNH.

## 7. Error handling
resume không có file → FileNotFoundError rõ ràng · digest lệch → ValueError
nêu 2 digest · checkpoint ghi lỗi → IOError lan lên.

## 8. Acceptance
- **DoD-1.4:** bài 12×6×4 — chạy liền mạch vs (chạy max_iter=30 có checkpoint
  → resume đến hội tụ): rho cuối GIỐNG TỪNG BIT, compliance/n_iter/history khớp.
  Test cả method direct LẪN cg.
- **Không hồi quy:** optimize3d không tham số mới cho kết quả GIỐNG TỪNG BIT
  bản 1.3 (so với giá trị chốt trong test hiện có — suite cũ xanh nguyên).
- **Digest:** resume bằng spec khác → ValueError.
- **Profiling:** history có t_solve/t_grad_filter/t_oc/rss_mb đủ độ dài n_iter.
- **Bộ đo laptop:** benchmark_laptop.py in verdict DoD-1.2 (hội tụ <150 vòng,
  <3600s) + DoD-1.3 (peak RSS <8GB), ghi bench/report_64x32x32.json.
  Sandbox chỉ chạy THĂM DÒ vài vòng lấy ước lượng — số chính thức của NGƯỜI.

## 9. Ngoài phạm vi
STL/FreeCAD (1.5) · render (1.6) · matrix-free CG (BACKLOG nếu DoD-1.3 fail).

---
## Phase 0 — câu 1–4 (MEDIUM)
1. **Output:** mục 3; `python -m pytest tests/ -v` (trừ benchmark CI) PASS.
2. **Không chạm:** 19 file protected còn lại; optimize3d theo nghi thức mở khóa.
3. **Dependencies:** psutil cài sandbox ✓ khi chạy; 125 test nền xanh.
4. **I/O:** checkpoint .npz (digest str, rho, u_prev, n_iter, history_json);
   optimize3d giữ nguyên chữ ký cũ + 3 tham số mới mặc định tắt.
