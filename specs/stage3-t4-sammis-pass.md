# SPEC: stage3-t4-sammis-pass

> Tầng 3.4 — DoD-3.3 dogfooding: toàn codebase pass chuẩn Sammis.

## 1-2. Mục tiêu & thiết kế
scripts/sammis_scan_all.py chạy scanner của chính sammis.py trên MỌI
.py trong repo (trừ .git, bench/agent_trials). Exit 0 = 0 BLOCK.

## Kết quả đo 16/07/2026
- Quét 51 file: BLOCK=0, WARN=1 (swallow-suspect optimize3d.py:26 —
  file protected, handler có hồ sơ từ Stage 1, không thuộc mức chặn).
- Full test suite sandbox: 209 passed / 0 failed (2 deselect chuẩn
  sandbox: dod_1_1 64³ + brake smoke — CI/laptop chạy đủ).
- preflight PASS (PYTHONUTF8=1).

## 8. Acceptance
DoD-3.3: scan-all exit 0. ✓
