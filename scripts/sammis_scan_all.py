"""DoD-3.3 — quét chuẩn Sammis TOÀN codebase (không chỉ file staged).

Dùng lại đúng scanner của sammis.py (một nguồn sự thật). Exit 0 khi
0 vi phạm mức chặn; 1 khi có BLOCK. Đo 16/07/2026: 50 file, BLOCK=0,
WARN=1 (swallow-suspect trong optimize3d.py protected — hồ sơ Stage 2).
"""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    spec = importlib.util.spec_from_file_location(
        "sammis", ROOT / "sammis.py")
    sm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sm)
    files = sorted(p for p in ROOT.rglob("*.py")
                   if ".git" not in p.parts
                   and "agent_trials" not in p.parts)
    findings = []
    for f in files:
        findings += sm.check_file(str(f), str(f.relative_to(ROOT)),
                                  str(ROOT))
    print(f"[scan-all] {len(files)} file .py")
    blocked = sm.print_findings(findings)
    print("[scan-all] " + ("CO VI PHAM MUC CHAN" if blocked
                           else "0 vi pham muc chan — DoD-3.3 PASS"))
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
