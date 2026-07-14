"""Entry point: `python -m geophys run <spec.json>` — DoD-2.5.

Chỉ lệnh `run` (Stage 2). `validate`/`report` thuộc Stage 3 — chưa mở.
Exit code: 0 thành công · 1 pipeline xong nhưng FAIL · 2 lỗi spec/tham số.
"""

from __future__ import annotations

import sys

from geophys.errors import SpecError

_USAGE = (
    "Cách dùng: python -m geophys run <spec.json> "
    "[--outdir DIR] [--method auto|direct|cg] [--max-iter N] "
    "[--resume-from CHECKPOINT.npz]"
)


def main(argv) -> int:
    if len(argv) < 2 or argv[0] != "run":
        print(_USAGE, file=sys.stderr)
        if argv and argv[0] in ("validate", "report"):
            print(f"Lệnh '{argv[0]}' thuộc Stage 3 — chưa mở.",
                  file=sys.stderr)
        return 2

    spec_path = argv[1]
    kwargs = {}
    i = 2
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


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
