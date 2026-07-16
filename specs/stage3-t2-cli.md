# SPEC: stage3-t2-cli

> Tầng 3.2 — CLI 3 lệnh chuẩn agent (S3.1 #1). Mức: LOW.
> Mở khóa: geophys/__main__.py (nghi thức — khóa lại ngay sau commit).

## 1. Mục tiêu
`geophys validate|run|report` — bộ ba đủ vòng đời cho agent: kiểm
trước, chạy, đọc kết quả. Exit code là HỢP ĐỒNG: 0 PASS · 1 FAIL · 2
lỗi spec/tham số/thiếu file. KHÔNG đổi nghĩa exit của `run` (DoD-2.5).

## 2. Thiết kế
validate → geophys.validate (3.1), JSON ra stdout kể cả khi rác (agent
parse một đường); report → đọc <outdir>/report.json của run đã xong,
in JSON, exit theo status. run giữ nguyên từng chữ logic 2.4.

## 3. Output (ĐÓNG)
geophys/__main__.py (viết lại) · tests/test_cli.py (5 test mới thay
test_lenh_stage3_bi_chan) · spec này.

## 8. Acceptance
test_cli 10/10: validate 0/2, report 0/2 + PASS sau run, run 4 nhánh cũ
nguyên vẹn, lệnh lạ exit 2.

## Phase 0 (LOW): dep không mới · lỗi không nuốt · staging.
