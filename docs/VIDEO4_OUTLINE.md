# Video 4 — "Tôi build engine thiết kế bằng vật lý — đây là cấu trúc nó tự mọc ra"
(DoD-3.4 — NGƯỜI quay + đăng. Kể chuẩn "mộc": cả cú vả lẫn khoảnh khắc thắng.)

## Cấu trúc 8-10 phút

1. HOOK (30s) — Cho xem media/brake_pedal_iso.png: "Không ai vẽ cái này.
   Vật lý vẽ. Tôi chỉ khai: 1200N, nhôm, 2 lỗ, giảm 55% vật liệu."
2. CÚ VẢ MỞ ĐẦU (1ph) — Thú nhận kế hoạch gốc từng mơ "safety factor
   1.0 tối ưu tuyệt đối" — và tại sao đó là mơ ngủ (variance vật liệu,
   in 3D, tải thật). Hợp đồng tự sửa: benchmark quốc tế là thước, không
   phải cảm quan.
3. STAGE 0 (1.5ph) — media/mbb_evolution.gif: 94 vòng từ khối đặc thành
   dàn — khớp chuẩn quốc tế top88 lệch 0.006%.
4. STAGE 1 (1.5ph) — GIF/STL cantilever 3D (media/cantilever3d_*.stl,
   viewer HTML xoay được). Cú vả kể thật: benchmark 64³ FAIL lần đầu
   (150 vòng dao động biên — rmin), WinError 32, FreeCAD ăn dấu tiếng
   Việt trong đường dẫn. Mỗi cú vả = một luật mới trong sổ.
5. STAGE 2 — TRẬN CHUNG KẾT (2.5ph) — Bàn đạp phanh: spec → chạy 65
   vòng trên laptop → STL → nạp FreeCAD/CalculiX (trọng tài độc lập,
   lưới mịn gấp 13 lần): VON MISES 72.18 MPa < 276 MPa, safety factor
   3.82, 0/93.763 node vượt yield. Cho xem bench/brake_verdict_vonmises.png
   — màu nóng đúng chỗ cơ học dự đoán (vành lỗ trục).
6. STAGE 3 — ĐÓNG HỘP (1.5ph) — Demo live 3 lệnh: validate (spec rác
   → JSON lỗi tự sửa) / run / report. Đề bài tiếng Việt → agent tự làm
   hết (bench/agent_trials/).
7. CTA (30s) — "Repo + STL mẫu ở link dưới. Nếu bạn có bài toán thật —
   giá đỡ, bracket, chi tiết in 3D — comment/inbox, tôi chạy thử miễn
   phí." (→ đổ vào phễu đo DoD-3.5.)

## Nguyên liệu sẵn trong repo
mbb_evolution.gif · cantilever3d viewer · brake_pedal_iso.png ·
brake_pedal_design_space.png · brake_verdict_vonmises.png · FCStd mở
live · agent_trials 3 bài · các con số: 0.006% / 0.028% / 115 vòng
25ph 718MB / 1.923 / 72.18 MPa / SF 3.82 / 209 test.
