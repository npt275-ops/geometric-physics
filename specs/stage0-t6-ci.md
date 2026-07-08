# SPEC: stage0-t6-ci

> Tầng 0.6 — hạng mục S0.1 #10. Mức rủi ro: LOW → Phase 0 câu 1–2.
> LƯU Ý PHÂN QUYỀN: agent chỉ SOẠN file CI + kiểm cú pháp cục bộ.
> Tạo repo GitHub, push, xác nhận CI xanh = việc của NGƯỜI VẬN HÀNH
> (deployment gate — mục "ba thứ không giao agent" trong quy chuẩn).

## 1. Mục tiêu
Workflow GitHub Actions chạy toàn bộ pytest trên matrix
Windows + Ubuntu × Python 3.11 + 3.12, PYTHONUTF8=1 (DoD-0.7).

## 2. Input
requirements.txt hiện hành (numpy, scipy, pytest, matplotlib, pillow) ·
79 test trong tests/.

## 3. Output (danh sách file ĐÓNG)
- `.github/workflows/ci.yml`
(spec này: `specs/stage0-t6-ci.md`)

## 4. Logic
Trigger: push nhánh main + pull_request. Job test: checkout → setup-python
→ pip install -r requirements.txt → `python -m pytest tests/ -v`.
fail-fast: false (một ô matrix đỏ không che các ô còn lại).

## 5. Dependencies
Cú pháp YAML kiểm cục bộ bằng parser Python. GitHub Actions runner — ngoài
tầm sandbox, thuộc bước xác nhận của người vận hành.

## 6. Không được phép
Chạm 13 file protected · sửa test để "cho CI dễ xanh".

## 7. Error handling
CI đỏ trên GitHub → đọc log ô matrix đỏ, sửa tại tầng gây lỗi (không vá trong ci.yml).

## 8. Acceptance
- Cục bộ (agent): YAML parse hợp lệ; tên job/step đầy đủ; matrix đúng 4 ô;
  PYTHONUTF8 khai trong env; `python -m pytest tests/ -v` local PASS (79/79).
- **DoD-0.7 (người vận hành):** push lên GitHub → 4/4 ô matrix xanh.
  Tầng 0.6 và Stage 0 CHỈ ĐÓNG khi có bằng chứng này.

## 9. Ngoài phạm vi
Badge README, release, publish PyPI, CD — không thuộc Giai đoạn 1.

---
## Phase 0 (LOW)
1. **Output:** 1 file ci.yml + spec; kiểm YAML + pytest local.
2. **Không chạm:** 13 file protected.
