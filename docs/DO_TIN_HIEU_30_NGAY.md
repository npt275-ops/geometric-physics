# Giao thức đo tín hiệu thị trường — DoD-3.5 (NGƯỜI vận hành)

NGUYÊN TẮC HỢP ĐỒNG: ĐO, không ĐOÁN. 30 ngày tính từ ngày video lên
sóng. Ghi MỌI phản hồi inbound vào bench/market_signals.csv ngay khi
xảy ra (đừng dựa trí nhớ cuối tháng).

## Cách ghi (mỗi dòng 1 tương tác)
- ngay: YYYY-MM-DD
- kenh: youtube-comment | inbox | group-fb | zalo | khac
- ai: ten/nick (đủ để nhận lại)
- phan_loai: sinh-vien | xuong-in-3d | ky-su | cong-ty | khac
- ho_muon_gi: 1 câu nguyên văn nhu cầu
- hoi_thoai_that: 1 nếu có trao đổi 2 chiều về BÀI TOÁN THẬT của họ
  (định nghĩa chặt: họ mô tả bài toán cụ thể của chính họ — không tính
  khen/hỏi xã giao); 0 nếu không
- ghi_chu

## Phán quyết (ngày 30)
- SUM(hoi_thoai_that) >= 5  → tín hiệu ĐÁNG CHÚ Ý: mở hồ sơ Cấp độ 2
  (parallel simulation) + cân nhắc GP Studio (BACKLOG) — bằng dữ liệu.
- < 5 → ĐÓNG BĂNG CÓ LÃI: GP = công cụ nội bộ X2 + content. KHÔNG
  build thêm tính năng cho thị trường chưa tồn tại (nguyên văn hợp đồng).
NGƯỜI ký phán quyết vào MANIFEST: "DoD-3.5: <số> hội thoại thật — <kết cục>".
