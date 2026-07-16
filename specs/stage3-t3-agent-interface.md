# SPEC: stage3-t3-agent-interface

> Tầng 3.3 ⭐ — Agent Interface + 3 bài thử trọn vòng (DoD-3.1, S3.1 #3).
> Mức: HIGH (đây là định nghĩa "đóng hộp"). Không mở khóa protected.

## 1. Mục tiêu
Một agent CHỈ ĐỌC AGENT.md (không đọc source) đủ để: nhận đề bài tiếng
Việt → viết spec.json → validate → run → report → TỰ ĐÁNH GIÁ. 3/3 bài
khác nhau thành công, không người can thiệp giữa chừng.

## 2. Thiết kế
- AGENT.md tại root: quy ước tọa độ/đơn vị mm-N-MPa, bảng vật liệu,
  3 lệnh CLI + exit code, mẫu spec v1/v2, link docs/spec_schema.json,
  và TIÊU CHÍ TỰ ĐÁNH GIÁ GHI TRƯỚC (S3-R3 — chống "tự chấm tự khen"):
  report.status == PASS ∧ converged ∧ |volume−volfrac| ≤ 1%·volfrac
  ∧ STL watertight ∧ 1 khối. Agent chấm đúng các tiêu chí này, không thêm bớt.
- 3 đề bài PHỦ 3 NHÁNH KHÁC NHAU của engine:
  B1 công-xôn 500N (v1, ngàm mặt, nhôm) · B2 dầm 2 gối 800N giữa nhịp
  (v1, ngàm node, thép, volfrac lạ 0.35) · B3 tấm treo 2 lỗ bu-lông
  (v2 ĐA CASE + preserve/void, titan).
- Bằng chứng: bench/agent_trials/bai{1,2,3}/{de_bai.txt, spec.json,
  out/, danh_gia.json} — sinh bằng đúng 3 lệnh CLI, log lại lệnh đã gõ.

## 3. Output (ĐÓNG)
AGENT.md · bench/agent_trials/** · tests/test_agent_trials.py (đọc lại
danh_gia.json + report.json xác nhận 3/3 tiêu chí) · spec này.

## 8. Acceptance
DoD-3.1: 3/3 bài PASS đủ tiêu chí ghi trước; NGƯỜI ký xác nhận "không
can thiệp giữa chừng" khi đóng stage.

## 9. Ngoài phạm vi
GP Studio · đề bài cần hình học cong chi tiết (voxel là mức Cấp độ 1).

## Phase 0 (HIGH): output mục 3 · không chạm protected · dep không mới
· I/O: NL → file JSON → exit codes · lỗi: validate chặn trước khi đốt
máy · staging.
