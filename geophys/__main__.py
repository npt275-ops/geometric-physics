"""Entry point CLI — 3 lệnh chuẩn cho agent (Stage 3, S3.1 #1).

  python -m geophys validate <spec.json>   — kiểm spec, JSON ra stdout
  python -m geophys run <spec.json> [...]  — chạy trọn pipeline (DoD-2.5)
  python -m geophys report <outdir>        — đọc report của run đã xong

Exit code (hợp đồng với agent — KHÔNG đổi nghĩa):
  0 thành công/PASS · 1 pipeline xong nhưng FAIL · 2 lỗi spec/tham số/thiếu file
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from geophys.errors import SpecError

_USAGE = (
    "Cách dùng:\n"
    "  python -m geophys validate <spec.json>\n"
    "  python -m geophys run <spec.json> [--outdir DIR] "
    "[--method auto|direct|cg] [--max-iter N] [--resume-from CKPT.npz]\n"
    "  python -m geophys report <outdir>"
)


def _cmd_validate(argv) -> int:
    if len(argv) != 1:
        print(_USAGE, file=sys.stderr)
        return 2
    from geophys.validate import validate_spec
    kq = validate_spec(argv[0])
    print(json.dumps(kq, ensure_ascii=False, indent=1))
    return 0 if kq["trang_thai"] == "HOP_LE" else 2


def _cmd_report(argv) -> int:
    if len(argv) != 1:
        print(_USAGE, file=sys.stderr)
        return 2
    duong_dan = Path(argv[0])
    f = duong_dan / "report.json" if duong_dan.is_dir() else duong_dan
    if not f.is_file():
        print(f"Không thấy report: {f} — outdir đã chạy "
              "`geophys run` chưa?", file=sys.stderr)
        return 2
    try:
        report = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"report.json hỏng: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0 if report.get("status") == "PASS" else 1


def _cmd_run(argv) -> int:
    if not argv:
        print(_USAGE, file=sys.stderr)
        return 2
    spec_path = argv[0]
    kwargs = {}
    i = 1
    try:
        while i < len(argv):
            flag = argv[i]
            if flag == "--outdir":
                kwargs["outdir"] = argv[i + 1]
            elif flag == "--method":
                kwargs["method"] = argv[i + 1]
            elif flag == "--max-iter":
                kwargs["max_iter"] = int(argv[i + 1])
            elif flag == "--resume-from":
                kwargs["resume_from"] = argv[i + 1]
            else:
                print(f"Tham số lạ: {flag}\n{_USAGE}", file=sys.stderr)
                return 2
            i += 2
    except (IndexError, ValueError):
        print(f"Tham số thiếu/sai giá trị.\n{_USAGE}", file=sys.stderr)
        return 2

    from geophys.runner import run_spec  # import muộn: lỗi spec báo đẹp
    try:
        code, _ = run_spec(spec_path, **kwargs)
    except SpecError as exc:
        print(f"SPEC LỖI: {exc}", file=sys.stderr)
        return 2
    return code


def main(argv) -> int:
    if not argv:
        print(_USAGE, file=sys.stderr)
        return 2
    lenh, phan_con = argv[0], argv[1:]
    if lenh == "validate":
        return _cmd_validate(phan_con)
    if lenh == "run":
        return _cmd_run(phan_con)
    if lenh == "report":
        return _cmd_report(phan_con)
    print(f"Lệnh lạ: {lenh}\n{_USAGE}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
