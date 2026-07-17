# SPEC: stage3-t6-gauntlet — GP GAUNTLET: 10 bài khảo tra hộp đen

> MỤC ĐÍCH HỒ SƠ: đây là BẰNG CHỨNG VỀ KHẢ NĂNG CỦA GP. Kế hoạch +
> kỳ vọng từng bài được ĐĂNG KÝ TRƯỚC (commit vào git TRƯỚC khi chạy
> bất kỳ bài nào — dấu thời gian git là trọng tài). Sau khi chạy,
> kết quả đối chiếu nguyên trạng: đúng thì là năng lực đã chứng minh,
> lệch thì là dữ liệu quý — KHÔNG nới tiêu chí hồi tố.

## 1. Mục tiêu
Chứng minh GP là engine ĐÓNG HỘP khó phá: agent chỉ dùng AGENT.md +
3 lệnh CLI (validate/run/report), không đọc source, vượt 10 bài phủ
vật lý đa dạng + biên khắc nghiệt + đường lỗi/vòng đời.

## 2. Luật chơi (hộp đen)
- Chỉ `python -m geophys validate|run|report` + AGENT.md + spec_schema.
- Lưới ≤ ~2.000 phần tử/bài (ràng buộc sandbox <45s).
- Chấm: 4 tiêu chí AGENT.md mục 4 + KỲ VỌNG VẬT LÝ GHI TRƯỚC (mục 4
  dưới đây) đo bằng SỐ trên report/STL — không cảm quan.
- Không chạm 31 file protected. Mọi bằng chứng vào bench/gauntlet/.

## 3. Ma trận 10 bài

| # | Bài | Nhánh kiểm | Vật liệu |
|---|---|---|---|
| 01 | Công-xôn tải lệch tâm góc | bất đối xứng 3D | nhôm 6061 |
| 02 | Dầm 2 gối tải 1/4 nhịp | bất đối xứng theo x | thép S235 |
| 03 | Cột nén dọc trục | tải hướng −y dọc trục | titan |
| 04 | Tấm mỏng chịu cắt fz | miền dẹt, biến dạng cắt | nhôm 6061 |
| 05 | Bracket chữ L (void cắt miền) + lỗ bu-lông | preserve/void định hình | thép S235 |
| 06 | Đa case 3 hướng w=1.0/0.5/0.3 | multi-load robustness | nhôm 6061 |
| 07 | Khan vật liệu volfrac 0.20 | hội tụ ngân sách gắt | titan |
| 08 | Preserve ~90% ngân sách | OC sát trần khả thi | nhôm 6061 |
| 09 | FAIL→resume (max-iter 5 → resume) | vòng đời, exit 1→0 | thép S235 |
| 10 | Agent tự sửa spec 2 lỗi chồng | vòng validate-sửa | nhôm 6061 |

## 4. KỲ VỌNG ĐĂNG KÝ TRƯỚC (đối chiếu sau khi chạy — cấm sửa)
- Chung (bài 01–08): validate exit 0 → run exit 0 → report exit 0;
  report PASS + converged; |vol − volfrac| ≤ 1%·volfrac; STL watertight
  1 khối.
- 01: khối lượng nửa z chứa điểm đặt lực > nửa còn lại (đo mean(rho)
  hai nửa, lệch > 2%).
- 02: khối lượng nửa x gần lực (chứa x=nelx/4) > nửa xa (lệch > 5%).
- 03: cột hội tụ; vật liệu phân bố dọc trục nén (mean rho cột giữa
  ≥ mean rho toàn miền).
- 04: PASS với miền dẹt nelz nhỏ; không lỗi solver.
- 05: voxel trong vùng void-L = 0 tuyệt đối mọi vòng (đọc rho cuối
  qua checkpoint hoặc suy từ STL bbox); vành preserve = 1.
- 06: chạy thêm bản single (case chính) — c₃(single) / c₃(multi) > 1
  (multi cứng hơn dưới tải ngang; không đặt ngưỡng 1.3 vì bài nhỏ,
  chỉ đòi ĐÚNG CHIỀU).
- 07: hội tụ được ở 0.20 và volume đúng 0.20 ± 1%·0.20.
- 08: validate phải CẢNH BÁO/CHẶN nếu preserve > volfrac (GP-E-PHYSICS)
  — bài này preserve ≈ 90% ngân sách (HỢP LỆ, không vượt): kỳ vọng
  PASS + volume đúng; đây là kiểm OC không vỡ khi tự do còn ~10%.
- 09: run --max-iter 5 → exit 1, report.json vẫn ĐỦ trường, status
  FAIL, converged=false; run --resume-from checkpoint → exit 0 PASS;
  report cuối n_iter > 5.
- 10: spec gieo ĐÚNG 2 lỗi (thiếu ngàm + preserve ngoài lưới); vòng
  sửa theo loi[].goi_y hội tụ HOP_LE trong ≤ 3 vòng validate; sau đó
  run PASS. Log đủ các phiên bản spec v1→vN.

## 5. Bằng chứng (ĐÓNG)
bench/gauntlet/bai01..10/{de_bai.txt, spec*.json, validate*.json,
out/, cham_diem.json} · bench/gauntlet/TONG_KET.md (bảng 10 dòng:
kỳ vọng vs đo được) · tests/test_gauntlet.py (chấm lại độc lập).

## 6. Không được phép
Sửa kỳ vọng mục 4 sau commit này · nới 4 tiêu chí AGENT.md · đọc
source engine để "lách" · chạm protected.

## 7. Error handling
Bài lệch kỳ vọng → ghi nguyên trạng vào TONG_KET.md, phân tích nguyên
nhân, KHÔNG chạy lại với tham số "dễ hơn" trừ khi ghi rõ là bài mới.

## 8. Acceptance
10/10 đúng kỳ vọng = GAUNTLET PASS. Bất kỳ lệch nào: báo cáo + NGƯỜI
quyết định bước tiếp.

## 9. Ngoài phạm vi
Lưới lớn laptop-scale · FreeCAD (đã có DoD-2.3) · benchmark thời gian.

---
## Phase 0 — 7 câu (MEDIUM)
1. Output: mục 5. 2. Không chạm: 31 protected. 3. Dep: không mới.
4. I/O: CLI thuần. 5. STABLE: chỉ gọi qua CLI. 6. Lỗi: mục 7.
7. Production? Staging — chiến dịch kiểm chứng.

---
## PHIÊN 2 — ĐĂNG KÝ SAU VÁ (16/07/2026, sau commit vá OC + validator)

Phiên 1: 9/10 + bài 08 lệch trung thực + bug resume bị bắt (TONG_KET.md).
NGƯỜI ra lệnh mục tiêu cuối: 10/10 — vá tận gốc, không chấm lại cho đẹp.
Đã vá: (a) OC giảm chấn dao động (optimize3d, golden trùng bit, nghi
thức mở khóa); (b) validator cảnh báo mềm GP-W-PHYSICS >70% ngân sách.

KỲ VỌNG PHIÊN 2 (đăng ký TRƯỚC khi tái khảo tra, cấm sửa):
- Bài 01–07, 09, 10: GIỮ NGUYÊN kỳ vọng mục 4 phiên 1, chạy lại TƯƠI
  từ đầu (xóa out cũ) trên engine đã vá.
- Bài 08 (kỳ vọng MỚI): validate HOP_LE + canh_bao[0].ma == GP-W-PHYSICS;
  run exit 0, PASS, converged, n_iter ≤ 200; |vol − 0.42| ≤ 1%·0.42;
  STL watertight 1 khối; biến thể vượt ngân sách vẫn bị CHẶN GP-E-PHYSICS.
  (Chấp nhận compliance cao hơn nghiệm dao động phiên 1 — ổn định và
  tất định là yêu cầu của thợ rèn, đo thí nghiệm: 302.25, 47 vòng.)
- Chiến dịch PASS khi và chỉ khi 10/10 ĐẠT phiên 2.
