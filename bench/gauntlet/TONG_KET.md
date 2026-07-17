# GP GAUNTLET — TỔNG KẾT (16/07/2026)

Kỳ vọng đăng ký trước tại specs/stage3-t6-gauntlet.md — **commit
`dddfa66` TRƯỚC khi chạy bài nào** (dấu thời gian git là trọng tài).
Agent chỉ dùng AGENT.md + 3 lệnh CLI. Giám khảo chấm bằng số đo trên
rho/report (checkpoint) — không cảm quan.

## Kết quả: 9/10 ĐẠT + 1 lệch trung thực + 1 bug bị bắt & vá

| # | Bài | Kỳ vọng | Đo được | Phán quyết |
|---|---|---|---|---|
| 01 | Công-xôn lệch tâm góc | bất đối xứng z > 2% | **lệch 392%** (0.665 vs 0.135) | ĐẠT |
| 02 | Dầm 2 gối tải 1/4 nhịp | nửa gần lực nặng hơn > 5% | **38.1%** (0.406 vs 0.294) | ĐẠT |
| 03 | Cột nén dọc trục | ρ cột giữa ≥ ρ toàn miền | **0.986 vs 0.300** — cột đặc đúng trục | ĐẠT |
| 04 | Tấm mỏng chịu cắt fz | PASS miền dẹt | PASS, hội tụ, STL kín | ĐẠT |
| 05 | Bracket chữ L + bu-lông | void = 0 tuyệt đối, vành = 1 | **max ρ void = 0.0 · min ρ vành = 1.0** | ĐẠT |
| 06 | Đa case 3 hướng | c₃(single)/c₃(multi) > 1 | **2.365** — single yếu hơn 136% dưới tải ngang | ĐẠT |
| 07 | Khan vật liệu 0.20 | hội tụ + volume 0.20 ±1% | volume **0.200000** | ĐẠT |
| 08 | Preserve ~89% ngân sách | PASS + volume đúng | **LỆCH**: 200 vòng không hội tụ (change dao động ~0.18), engine trung thực FAIL exit 1, volume vẫn 0.42, không crash. Biến thể VƯỢT ngân sách bị validator chặn đúng GP-E-PHYSICS ✓ | LỆCH (ghi nguyên trạng) |
| 09 | FAIL → resume | exit 1 đủ report → resume exit 0 | exit 1 ✓ report đủ trường ✓ → **BUG resume-tại-chỗ SameFileError bị bắt** → vá theo nghi thức (runner.py, +test hồi quy) → resume PASS 42 vòng ✓ | ĐẠT (kèm chiến lợi phẩm bug) |
| 10 | Agent tự sửa 2 lỗi chồng | HỢP LỆ trong ≤3 vòng → PASS | đúng **3 vòng** (PHYSICS→GEOMETRY→HỢP LỆ), run PASS | ĐẠT |

## Phân tích 2 phát hiện (giá trị thật của gauntlet)

**Bài 08 — giới hạn được ĐO:** khi preserve ngốn ~89% ngân sách volfrac,
OC chỉ còn ~11% tự do và dao động không hội tụ (change kẹt ~0.18,
compliance nhấp nhô 235⇄237). Engine xử đúng thiết kế: không crash,
không nói dối, FAIL exit 1 + report đầy đủ. Bài học sản phẩm: agent
nên giữ preserve dưới ~70-80% ngân sách; validator hiện chặn VƯỢT
(GP-E-PHYSICS) — có thể thêm CẢNH BÁO ngưỡng mềm (ghi BACKLOG, không
sửa hồi tố).

**Bài 09 — bug thật đầu tiên sau 209 test:** `--resume-from` trỏ vào
chính checkpoint trong `--outdir` (thao tác tự nhiên nhất của agent)
nổ SameFileError. Vá 1 dòng (bỏ copy khi src==đích) + test hồi quy
`test_resume_tai_cho_khong_no`. Đây là lý do gauntlet tồn tại.

## Ý nghĩa hồ sơ
10 bài phủ: 3 vật liệu · 5 dạng tải (uốn/lệch tâm/nén/cắt/đa hướng) ·
preserve/void định hình + lỗ bu-lông · biên ngân sách 0.20 · đường
FAIL/resume · vòng agent-tự-sửa-spec. Engine đóng hộp trả lời đúng
mọi đường — kể cả đường xấu — bằng exit code và report máy-đọc-được.

---
# PHIÊN 2 — SAU KHI KHÓA LỖ HỔNG (16/07/2026, đăng ký 12346dd)

Lệnh NGƯỜI: mục tiêu cuối 10/10 — vá tận gốc, không chấm lại cho đẹp.
Hai bản vá (đều qua nghi thức mở khóa, golden trùng bit):
1. **OC giảm chấn dao động** (optimize3d.py): 3 điều kiện kích hoạt
   (≥vòng 40 + change đi ngang trên tol + compliance đổi dấu ≥4 lần)
   → halve move, sàn 0.005. Bài hội tụ bình thường không bao giờ chạm
   nhánh này — G1/G2 trùng bit, toàn suite xanh.
2. **Validator cảnh báo mềm** GP-W-PHYSICS khi preserve >70% ngân sách.

## Tái khảo tra TƯƠI 10 bài (xóa toàn bộ out cũ): **10/10 ĐẠT**

| # | Số đo phiên 2 | Phán quyết |
|---|---|---|
| 01 | bất đối xứng z 392% | ĐẠT |
| 02 | dồn về gối gần lực 38.1% | ĐẠT |
| 03 | ρ cột giữa 0.986 vs 0.300 | ĐẠT |
| 04 | PASS miền dẹt | ĐẠT |
| 05 | void max 0.0 · vành min 1.0 | ĐẠT |
| 06 | tỷ số c₃ 2.367 | ĐẠT |
| 07 | volume 0.200000 | ĐẠT |
| 08 | **PASS 47 vòng** (trước: FAIL 200 vòng dao động) + cảnh báo GP-W đúng chỗ + biến thể vượt vẫn bị chặn | **ĐẠT** |
| 09 | exit 1 → resume tại chỗ exit 0, 42 vòng (bug đã vá) | ĐẠT |
| 10 | tự sửa đúng 3 vòng → PASS | ĐẠT |

**GAUNTLET PASS 10/10 — Thợ Rèn Trọng Lực đạt mục tiêu cuối.**
Chuỗi bằng chứng: kỳ vọng phiên 1 (dddfa66) → 9/10 + 2 phát hiện →
vá có kỷ luật → kỳ vọng phiên 2 (12346dd) → 10/10. Không một tiêu chí
nào được nới hồi tố; mọi thay đổi engine đều qua nghi thức và giữ
golden trùng bit.
