#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════
# QUY CHUẨN SAMMIS AGENT CODE V5 — sammis.py
# MỘT FILE DUY NHẤT · thuần stdlib · chạy y hệt trên Windows / macOS / Linux
#
# Gộp toàn bộ tầng cưỡng chế: trạm gác AST + đối chiếu Git + md5 protected
# + harness đo lường + git hook.
#
#   python sammis.py init        # cài vào repo (1 lần): template + git hook
#   python sammis.py preflight   # trước khi gọi agent: môi trường sẵn sàng?
#   python sammis.py snapshot    # chụp md5 file protected
#   python sammis.py risk        # mức rủi ro → Phase 0 nông/sâu
#   python sammis.py postagent   # sau khi agent xong: đối chiếu + quét + tự ghi số
#   python sammis.py report      # tỉ lệ đúng-ngay-lần-đầu THẬT của bạn
#   python sammis.py precommit   # (git hook tự gọi — không cần gọi tay)
#
# Yêu cầu: Git + Python 3.8+. Không cài thêm bất kỳ thư viện nào.
# ═══════════════════════════════════════════════════════════════════
import argparse
import ast
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

# ── Màu (tự bật ANSI trên Windows 10+, tắt bằng biến môi trường NO_COLOR) ──
if os.name == "nt":
    os.system("")
_C = not os.environ.get("NO_COLOR")
RED = "\033[31m" if _C else ""
GRN = "\033[32m" if _C else ""
YLW = "\033[33m" if _C else ""
BLD = "\033[1m" if _C else ""
RST = "\033[0m" if _C else ""


# ── Git helpers (đa nền tảng, an toàn với tên file có khoảng trắng) ──
def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def git_z(*args):
    r = subprocess.run(["git", *args], capture_output=True)
    return [p.decode("utf-8", "replace") for p in r.stdout.split(b"\0") if p]


def repo_root():
    rc, out = git("rev-parse", "--show-toplevel")
    return out.strip() if rc == 0 else None


# ── Trạng thái chung của một lần chạy ──
class G:
    fail = 0
    warns = 0
    fcodes = []


def ok(msg):
    print(f"{GRN}\u2713{RST} {msg}")


def ko(msg, code=None):
    print(f"{RED}\u2717{RST} {msg}")
    G.fail = 1
    if code:
        G.fcodes.append(code)


def wr(msg):
    print(f"{YLW}!{RST} {msg}")
    G.warns += 1


def summary():
    print("─" * 30)
    if G.fail:
        print(f"{RED}{BLD}VERIFY FAIL{RST} — sửa lỗi \u2717 trước khi đi tiếp")
        sys.exit(1)
    print(f"{GRN}{BLD}VERIFY PASS{RST} (cảnh báo: {G.warns})")


# ── Đường dẫn chuẩn (đặt sau khi xác định root trong main) ──
ROOT = ""
SAMMIS = ""


def p_profile():   return os.path.join(SAMMIS, "profile.env")
def p_protected(): return os.path.join(SAMMIS, "protected.list")
def p_snapshot():  return os.path.join(SAMMIS, "snapshot.md5")
def p_runs():      return os.path.join(SAMMIS, "runs")
def p_metrics():   return os.path.join(SAMMIS, "metrics.jsonl")


def load_profile():
    """Đọc profile.env dạng KEY="value" / KEY=value; nạp vào os.environ
    (setdefault — biến môi trường thật của người dùng luôn thắng)."""
    cfg = {}
    if not os.path.isfile(p_profile()):
        return cfg
    pat = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"?(.*?)"?\s*$')
    with open(p_profile(), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = pat.match(line)
            if m:
                cfg[m.group(1)] = m.group(2)
                os.environ.setdefault(m.group(1), m.group(2))
    return cfg


def changed_files():
    """Nguồn sự thật là Git: tracked-modified + staged + untracked."""
    files = set()
    rc, _ = git("rev-parse", "--verify", "HEAD")
    if rc == 0:
        files |= set(git_z("diff", "--name-only", "-z", "HEAD"))
    files |= set(git_z("diff", "--cached", "--name-only", "-z"))
    files |= set(git_z("ls-files", "--others", "--exclude-standard", "-z"))
    return sorted(f for f in files
                  if f and not f.replace("\\", "/").startswith(".sammis/"))


def protected_paths():
    if not os.path.isfile(p_protected()):
        return []
    out = []
    with open(p_protected(), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                out.append(line)
    return out


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


SECRET_NAME = re.compile(
    r"(api[_-]?key|secret|passw(or)?d|token|private[_-]?key|access[_-]?key)", re.I
)
PLACEHOLDER = {"", "changeme", "change-me", "your-key-here", "xxx",
               "placeholder", "...", "todo", "tbd"}
SKIP_DECORATORS = {"abstractmethod", "abstractproperty", "overload"}
BLOCKING_MODULES = {"requests", "urllib"}   # gọi trong async → cảnh báo


def is_placeholder(v: str) -> bool:
    s = v.strip().lower()
    return s in PLACEHOLDER or s.startswith(("<", "${", "env:", "{{"))


def decorator_name(d):
    if isinstance(d, ast.Name):
        return d.id
    if isinstance(d, ast.Attribute):
        return d.attr
    if isinstance(d, ast.Call):
        return decorator_name(d.func)
    return ""


class Checker(ast.NodeVisitor):
    def __init__(self, path, display_path, repo_root):
        self.path = path
        self.display = display_path
        self.root = repo_root
        self.findings = []
        self.async_depth = 0
        self.is_test = "test" in display_path.lower()

    def add(self, level, code, node, msg):
        self.findings.append({
            "level": level, "code": code, "file": self.display,
            "line": getattr(node, "lineno", 0), "msg": msg,
        })

    # ── 1. SILENT EXCEPTION (BLOCK) + SWALLOW-SUSPECT (WARN) ────
    def visit_ExceptHandler(self, node):
        body = [n for n in node.body
                if not (isinstance(n, ast.Expr)
                        and isinstance(n.value, ast.Constant)
                        and isinstance(n.value.value, str))]  # bỏ docstring lạc
        silent = all(
            isinstance(n, ast.Pass)
            or (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                and n.value.value is Ellipsis)
            for n in body
        ) if body else True
        if silent:
            what = "bare except" if node.type is None else "except ...:"
            self.add("BLOCK", "silent-except", node,
                     f"{what} chỉ có pass/... — lỗi bị nuốt im lặng")
        else:
            # Vá S6: handler có lệnh nhưng KHÔNG raise và KHÔNG gọi hàm nào
            # (không log, không xử lý) → nghi nuốt lỗi trá hình
            # Raise = đẩy lỗi lên · Call = có xử lý (log...) · Return = quyết
            # định tường minh trả sentinel. Chỉ nghi khi KHÔNG có cả ba.
            has_signal = any(
                isinstance(n, (ast.Raise, ast.Call, ast.Return))
                for stmt in body for n in ast.walk(stmt)
            )
            if not has_signal:
                self.add("WARN", "swallow-suspect", node,
                         "handler không raise và không gọi hàm nào (không log, "
                         "không xử lý) — nghi nuốt lỗi trá hình; xem Spec mục 7")
        self.generic_visit(node)

    # ── 2. HARDCODE CREDENTIAL (BLOCK) ──────────────────────────
    @staticmethod
    def _fold_str(node):
        """Gấp biểu thức chuỗi tĩnh về một giá trị: Constant, nối chuỗi
        bằng +, và f-string toàn literal. Trả None nếu có phần động."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            l = Checker._fold_str(node.left)
            r = Checker._fold_str(node.right)
            if l is not None and r is not None:
                return l + r
        if isinstance(node, ast.JoinedStr):
            parts = []
            for v in node.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    parts.append(v.value)
                elif isinstance(v, ast.FormattedValue):
                    inner = Checker._fold_str(v.value)
                    if inner is None:
                        return None  # có biến động — không kết luận được
                    parts.append(inner)
                else:
                    return None
            return "".join(parts)
        return None

    def _check_secret(self, name, value_node, node):
        if not (name and SECRET_NAME.search(name)):
            return
        folded = self._fold_str(value_node)
        if folded is not None and not is_placeholder(folded):
            self.add("BLOCK", "hardcode-credential", node,
                     f"'{name}' gán chuỗi cứng — đọc từ config/env thay vì nhúng vào code")

    def visit_Assign(self, node):
        for t in node.targets:
            name = t.id if isinstance(t, ast.Name) else (
                t.attr if isinstance(t, ast.Attribute) else None)
            self._check_secret(name, node.value, node)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if node.value is not None:
            t = node.target
            name = t.id if isinstance(t, ast.Name) else (
                t.attr if isinstance(t, ast.Attribute) else None)
            self._check_secret(name, node.value, node)
        self.generic_visit(node)

    def visit_Dict(self, node):
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                self._check_secret(k.value, v, node)
        self.generic_visit(node)

    # ── 3. GHOST IMPORT (BLOCK) ─────────────────────────────────
    def _search_dirs(self):
        return [self.root, os.path.dirname(self.path) or ".",
                os.path.join(self.root, "src")]

    def _local_top_exists(self, top):
        for d in self._search_dirs():
            if os.path.isfile(os.path.join(d, top + ".py")) \
                    or os.path.isdir(os.path.join(d, top)):
                return True
        return False

    def _local_full_exists(self, dotted):
        parts = dotted.split(".")
        for d in self._search_dirs():
            base = os.path.join(d, *parts)
            if os.path.isfile(base + ".py") or os.path.isdir(base):
                return True
        return False

    def _resolvable(self, dotted):
        top = dotted.split(".")[0]
        if self._local_top_exists(top):
            # Module local: đối chiếu ĐẦY ĐỦ đường dẫn — modules/ tồn tại
            # không có nghĩa modules/agent5.py tồn tại
            return self._local_full_exists(dotted)
        try:
            return importlib.util.find_spec(top) is not None
        except (ImportError, ValueError, AttributeError, ModuleNotFoundError):
            return False

    def visit_Import(self, node):
        for alias in node.names:
            if not self._resolvable(alias.name):
                self.add("BLOCK", "ghost-import", node,
                         f"import '{alias.name}' — module không tồn tại "
                         f"(chưa build hoặc chưa cài; đối chiếu MANIFEST mục NOT BUILT)")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.level == 0 and node.module:
            top = node.module.split(".")[0]
            if not self._resolvable(node.module):
                self.add("BLOCK", "ghost-import", node,
                         f"from '{node.module}' import ... — module không tồn tại")
            elif self._local_top_exists(top):
                # from modules import agent5 → agent5 có thể là submodule chưa build
                for alias in node.names:
                    sub = f"{node.module}.{alias.name}"
                    if not self._local_full_exists(sub):
                        # có thể là tên hàm/class trong __init__ — chỉ block khi
                        # module cha là package thư mục và không có file con
                        pass  # giữ mức an toàn: không block tên hàm hợp lệ
        elif node.level >= 1:
            base = os.path.dirname(self.path)
            for _ in range(node.level - 1):
                base = os.path.dirname(base) or "."
            if node.module:
                parts = node.module.split(".")
                cand_py = os.path.join(base, *parts) + ".py"
                cand_pkg = os.path.join(base, *parts)
                if not (os.path.isfile(cand_py) or os.path.isdir(cand_pkg)):
                    self.add("BLOCK", "ghost-import", node,
                             f"from {'.' * node.level}{node.module} import ... — "
                             f"đường dẫn tương đối không tồn tại")
        self.generic_visit(node)

    # ── 4. STUB FUNCTION (WARN) ─────────────────────────────────
    def _check_stub(self, node):
        if self.is_test:
            return
        if any(decorator_name(d) in SKIP_DECORATORS for d in node.decorator_list):
            return
        body = list(node.body)
        if body and isinstance(body[0], ast.Expr) \
                and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            body = body[1:]  # bỏ docstring
        if not body:
            return
        def _is_stub_stmt(n):
            if isinstance(n, ast.Pass):
                return True
            if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) \
                    and n.value.value is Ellipsis:
                return True
            if isinstance(n, ast.Raise):
                exc = n.exc
                nm = ""
                if isinstance(exc, ast.Call):
                    nm = decorator_name(exc.func)
                elif isinstance(exc, ast.Name):
                    nm = exc.id
                return nm == "NotImplementedError"
            if isinstance(n, ast.Return) and isinstance(n.value, ast.Constant) \
                    and n.value.value in ("placeholder", None) \
                    and isinstance(n.value.value, str):
                return True
            return False
        if all(_is_stub_stmt(n) for n in body):
            self.add("WARN", "stub-function", node,
                     f"'{node.name}' là stub (pass/.../NotImplementedError) — "
                     f"tên có, việc thật chưa có")

    def visit_FunctionDef(self, node):
        self._check_stub(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._check_stub(node)
        self.async_depth += 1
        self.generic_visit(node)
        self.async_depth -= 1

    # ── 5. ASYNC BLOCKING (WARN) ────────────────────────────────
    def visit_Call(self, node):
        # keyword secret: client(api_key="sk-...")
        for kw in node.keywords:
            if kw.arg:
                self._check_secret(kw.arg, kw.value, node)
        if self.async_depth > 0:
            f = node.func
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
                mod, attr = f.value.id, f.attr
                if mod == "time" and attr == "sleep":
                    self.add("WARN", "async-blocking", node,
                             "time.sleep trong hàm async — treo event loop; "
                             "dùng await asyncio.sleep")
                elif mod in BLOCKING_MODULES:
                    self.add("WARN", "async-blocking", node,
                             f"{mod}.{attr} (blocking I/O) trong hàm async — "
                             f"dùng httpx.AsyncClient / aiohttp")
        self.generic_visit(node)


def check_file(path, display, root):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            src = fh.read()
    except OSError as e:
        return [{"level": "BLOCK", "code": "read-error", "file": display,
                 "line": 0, "msg": str(e)}]
    try:
        tree = ast.parse(src, filename=display)
    except SyntaxError as e:
        return [{"level": "BLOCK", "code": "syntax-error", "file": display,
                 "line": e.lineno or 0, "msg": e.msg or "syntax error"}]
    c = Checker(path, display, root)
    c.visit(tree)
    return c.findings


def print_findings(findings):
    for x in findings:
        col = RED if x["level"] == "BLOCK" else YLW
        mark = "\u2717" if x["level"] == "BLOCK" else "!"
        print(f"{col}{mark} [{x['code']}] {x['file']}:{x['line']} — {x['msg']}{RST}")
    blocks = [x for x in findings if x["level"] == "BLOCK"]
    warns = [x for x in findings if x["level"] == "WARN"]
    if findings:
        print(f"— BLOCK={len(blocks)} WARN={len(warns)}")
    else:
        print(f"{GRN}\u2713 AST scan sạch{RST}")
    return blocks


# ═══════════════ METRICS (harness đo — Chương 8) ═══════════════
def metrics_read():
    if not os.path.isfile(p_metrics()):
        return []
    rows = []
    with open(p_metrics(), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"{YLW}! metrics.jsonl có dòng hỏng (bỏ qua): {e}{RST}")
    return rows


def metrics_log(task, result, codes):
    rows = metrics_read()
    attempt = sum(1 for r in rows if r.get("task") == task) + 1
    entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "task": task, "result": result, "attempt": attempt,
             "codes": sorted(set(codes))}
    with open(p_metrics(), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    tag = "ĐÚNG" if result == "pass" else "FAIL"
    print(f"[metrics] {task} · lần {attempt} · {tag}"
          + (f" · lỗi: {','.join(entry['codes'])}" if entry["codes"] else ""))


def cmd_report(md_path=None):
    rows = metrics_read()
    if not rows:
        print("Chưa có dữ liệu. Chạy vài task qua 'python sammis.py postagent' rồi quay lại.")
        return
    tasks = {}
    for r in rows:
        tasks.setdefault(r["task"], []).append(r)
    for v in tasks.values():
        v.sort(key=lambda r: r["attempt"])
    n = len(tasks)
    first_pass = [t for t, v in tasks.items() if v[0]["result"] == "pass"]
    rate = 100.0 * len(first_pass) / n
    green, att = 0, []
    for v in tasks.values():
        passes = [r for r in v if r["result"] == "pass"]
        if passes:
            green += 1
            att.append(passes[0]["attempt"])
    avg = sum(att) / len(att) if att else 0
    freq = {}
    for r in rows:
        if r["result"] == "fail":
            for c in r.get("codes") or ["khong-ro-loai"]:
                freq[c] = freq.get(c, 0) + 1
    ordered = sorted(tasks.values(), key=lambda v: v[0]["ts"])
    last10 = ordered[-10:]
    r10 = 100.0 * sum(1 for v in last10 if v[0]["result"] == "pass") / len(last10)

    L = ["# BÁO CÁO ĐO LƯỜNG — Quy chuẩn Sammis Agent Code",
         f"\nDữ liệu: {len(rows)} lần chạy · {n} task · nguồn: .sammis/metrics.jsonl\n",
         f"## Tỉ lệ ĐÚNG NGAY LẦN ĐẦU: **{rate:.0f}%** ({len(first_pass)}/{n} task)",
         f"- 10 task gần nhất: **{r10:.0f}%**",
         f"- Task đã xanh (kể cả retry): {green}/{n} · số lần trung bình để xanh: {avg:.1f}",
         "\n## Lỗi gặp nhiều nhất (ưu tiên cơ học hoá tiếp theo Chương 8)\n"]
    if freq:
        L += ["| Loại lỗi | Số lần |", "|---|---|"]
        L += [f"| {c} | {k} |" for c, k in sorted(freq.items(), key=lambda x: -x[1])]
    else:
        L.append("Chưa ghi nhận lỗi nào.")
    L += ["\n## Chi tiết theo task\n",
          "| Task | Lần đầu | Số lần chạy | Trạng thái cuối | Lỗi đã gặp |",
          "|---|---|---|---|---|"]
    for t, v in sorted(tasks.items(), key=lambda x: x[1][0]["ts"]):
        first = "\u2705" if v[0]["result"] == "pass" else "\u274c"
        final = "xanh" if any(r["result"] == "pass" for r in v) else "ĐỎ"
        codes = sorted({c for r in v for c in (r.get("codes") or [])})
        L.append(f"| {t} | {first} | {len(v)} | {final} | {', '.join(codes) or '—'} |")
    L.append("\n> Con số ở trên là ĐO, không phải hứa. Mỗi lỗi lặp lại phải trở"
             "\n> thành một check mới — đó là vòng tiến hoá Chương 8.")
    txt = "\n".join(L)
    if md_path:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(txt + "\n")
        print(f"[metrics] đã xuất báo cáo → {md_path}")
    else:
        print(txt)


# ═══════════════ PREFLIGHT ═══════════════
def cmd_preflight():
    print(f"{BLD}── PREFLIGHT ──{RST}")
    ok("git repo")
    cfg = load_profile()
    if cfg:
        ok("profile.env")
    else:
        wr("chưa có .sammis/profile.env — chạy 'python sammis.py init' hoặc tự tạo")

    exp = os.environ.get("EXPECTED_PYTHON", "")
    if exp:
        pv = ".".join(map(str, sys.version_info[:3]))
        if pv.startswith(exp):
            ok(f"python {pv} (khớp {exp})")
        else:
            ko(f"python {pv} ≠ EXPECTED_PYTHON={exp}")

    for v in os.environ.get("REQUIRED_ENV_VARS", "").split():
        if os.environ.get(v):
            ok(f"env ${v}")
        else:
            ko(f"thiếu env ${v}")

    sc = os.environ.get("SERVICE_CHECKS", "")
    if sc:
        for part in sc.split(";;"):
            part = part.strip()
            if not part:
                continue
            bits = part.split("|")
            if len(bits) != 3:
                wr(f"SERVICE_CHECKS sai định dạng: {part}")
                continue
            name, cmd, expect = (b.strip() for b in bits)
            try:
                r = subprocess.run(cmd, shell=True, capture_output=True,
                                   text=True, encoding="utf-8",
                                   errors="replace", timeout=30)
                out = (r.stdout or "") + (r.stderr or "")
            except (subprocess.SubprocessError, OSError) as e:
                ko(f"service {name} lỗi khi chạy lệnh ({e})")
                continue
            if expect in out:
                ok(f"service {name}")
            else:
                ko(f"service {name} không phản hồi đúng (lệnh: {cmd})")

    for f in ("MANIFEST.md", "CONTEXT.md"):
        if os.path.isfile(f):
            ok(f)
        else:
            wr(f"thiếu {f} — agent sẽ tự suy đoán (nguồn lỗi Ảo)")
    if os.path.isdir("specs"):
        ok("specs/")
    else:
        wr("thiếu specs/ — không spec = không gọi agent")

    prot = protected_paths()
    if os.path.isfile(p_protected()):
        for p in prot:
            if not os.path.isfile(p):
                wr(f"protected.list: '{p}' không tồn tại trên đĩa")
        # Cơ học hoá bất biến 5: MANIFEST (STABLE) ↔ protected.list không drift
        if os.path.isfile("MANIFEST.md"):
            with open("MANIFEST.md", encoding="utf-8") as f:
                for line in f:
                    if "|" in line and "STABLE" in line.upper():
                        cells = [c.strip() for c in line.split("|")]
                        if len(cells) > 1 and re.search(
                                r"\.(py|js|ts|sh|json|ya?ml)$", cells[1]):
                            if cells[1] not in prot:
                                wr(f"MANIFEST khai '{cells[1]}' là STABLE nhưng "
                                   f"chưa nằm trong protected.list")
    else:
        wr("chưa có protected.list — không có file nào được canh gác")
    summary()


# ═══════════════ SNAPSHOT ═══════════════
def cmd_snapshot():
    print(f"{BLD}── SNAPSHOT ──{RST}")
    if not os.path.isfile(p_protected()):
        ko(f"chưa có {p_protected()}")
        summary()
        return
    n = 0
    with open(p_snapshot(), "w", encoding="utf-8") as out:
        for p in protected_paths():
            if os.path.isfile(p):
                out.write(f"{md5_of(p)}  {p}\n")
                n += 1
            else:
                wr(f"bỏ qua '{p}' (không tồn tại)")
    ok(f"đã chụp md5 của {n} file protected → .sammis/snapshot.md5")
    summary()


def snapshot_violations():
    """Trả về danh sách file protected bị đổi/mất so với snapshot."""
    bad = []
    with open(p_snapshot(), encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            h, path = line.split("  ", 1)
            if not os.path.isfile(path):
                bad.append(f"{path} (đã bị xoá)")
            elif md5_of(path) != h:
                bad.append(f"{path} (nội dung đã đổi)")
    return bad


# ═══════════════ RISK ═══════════════
def cmd_risk():
    load_profile()
    ch = changed_files()
    level = "LOW"
    if len(ch) > 3:
        level = "MEDIUM"
    prot = set(protected_paths())
    if any(f in prot for f in ch):
        level = "HIGH"
    if os.environ.get("APP_ENV", "") == "production":
        level = "HIGH"
    ov = os.environ.get("RISK_OVERRIDE", "")
    if ov == "HIGH":
        level = "HIGH"
    elif ov == "MEDIUM" and level == "LOW":
        level = "MEDIUM"
    print(f"RISK={level} (file thay đổi: {len(ch)}; "
          f"APP_ENV={os.environ.get('APP_ENV', '?')}; OVERRIDE={ov or 'không'})")
    print("→ Phase 0: LOW = câu 1-2 · MEDIUM = câu 1-4 · HIGH = đủ 7 câu, rỗng = dừng cứng")


# ═══════════════ POSTAGENT ═══════════════
def cmd_postagent():
    print(f"{BLD}── POSTAGENT ──{RST}")
    load_profile()

    # 1. Declaration: run manifest mới nhất (mỗi run một file → không race)
    runs = []
    if os.path.isdir(p_runs()):
        runs = [os.path.join(p_runs(), f) for f in os.listdir(p_runs())
                if f.endswith(".json")]
    run = max(runs, key=os.path.getmtime) if runs else None
    if not run:
        ko("agent chưa xuất run manifest (.sammis/runs/*.json) — "
           "không có lời khai để đối chiếu", "no-manifest")
        _autolog("khong-ten")
        summary()
        return
    ok(f"run manifest: {os.path.relpath(run, ROOT)}")
    try:
        with open(run, encoding="utf-8") as f:
            decl = json.load(f)
        claimed = set(decl.get("files_created", []) + decl.get("files_modified", []))
        task = decl.get("task", "khong-ten")
    except (json.JSONDecodeError, OSError):
        ko("run manifest không phải JSON hợp lệ", "bad-manifest")
        _autolog("khong-ten")
        summary()
        return

    # 2. Discovery: Git nói gì — đối chiếu hai chiều
    actual = set(changed_files())
    creep = sorted(actual - claimed)
    unseen = sorted(claimed - actual)
    if creep:
        ko("SCOPE CREEP — file thay đổi NGOÀI lời khai của agent:", "scope-creep")
        for f in creep:
            print(f"    {f}")
    else:
        ok("scope khớp: mọi file thay đổi đều nằm trong lời khai")
    if unseen:
        wr("agent khai đã đụng nhưng Git không thấy thay đổi: " + " ".join(unseen))

    # 3. Protected: md5 phải nguyên vẹn so với snapshot
    if os.path.isfile(p_snapshot()):
        bad = snapshot_violations()
        if bad:
            ko("FILE PROTECTED BỊ SỬA:", "protected-tampered")
            for b in bad:
                print(f"    {b}")
        else:
            ok("mọi file protected nguyên vẹn (md5 khớp snapshot)")
    else:
        wr("chưa có snapshot — chạy 'python sammis.py snapshot' TRƯỚC khi gọi agent lần sau")

    # 4. AST scan mọi file .py vừa thay đổi
    pyfiles = [f for f in sorted(actual) if f.endswith(".py") and os.path.isfile(f)]
    if pyfiles:
        findings = []
        for f in pyfiles:
            findings += check_file(f, f, ROOT)
        blocks = print_findings(findings)
        if blocks:
            ko("AST scan phát hiện anti-pattern mức BLOCK (chi tiết ở trên)")
            G.fcodes += sorted({b["code"] for b in blocks})
        else:
            ok("AST scan: không có lỗi mức BLOCK")
    else:
        ok("không có file .py thay đổi để quét")

    # 5. Tests agent khai: liệt kê; chỉ tự chạy khi AUTORUN_TESTS=1
    tests = decl.get("tests_to_run", []) or []
    if tests:
        if os.environ.get("AUTORUN_TESTS", "0") == "1":
            for t in tests:
                print(f"  → chạy: {t}")
                r = subprocess.run(t, shell=True)
                if r.returncode == 0:
                    ok(f"test pass: {t}")
                else:
                    ko(f"test FAIL: {t}", "test-fail")
        else:
            wr("tests agent khai (chưa tự chạy — đặt AUTORUN_TESTS=1 trong profile để tự chạy):")
            for t in tests:
                print(f"    {t}")

    # 6. Cơ học hoá việc đo (Chương 8): tự ghi kết quả
    _autolog(task)
    summary()


def _autolog(task):
    try:
        metrics_log(task, "fail" if G.fail else "pass", G.fcodes)
    except OSError as e:
        wr(f"không ghi được metrics ({e}) — số liệu lần này bị thiếu")


# ═══════════════ PRE-COMMIT (git hook tự gọi) ═══════════════
def cmd_precommit():
    staged = git_z("diff", "--cached", "--name-only", "-z", "--diff-filter=ACM")
    if not staged:
        return
    print("── Sammis pre-commit V5 ──")
    block = False

    prot = set(protected_paths())
    for f in staged:
        if f in prot:
            print(f"{RED}\u2717 [{f}] nằm trong protected.list — CHẶN{RST}")
            print("  (nếu ĐÚNG là bạn chủ động sửa: cập nhật MANIFEST + protected.list"
                  " trước, rồi chạy 'python sammis.py snapshot' lại)")
            block = True

    pystaged = [f for f in staged if f.endswith(".py")]
    if pystaged:
        tmp = tempfile.mkdtemp(prefix="sammis-")
        try:
            findings = []
            for f in pystaged:
                r = subprocess.run(["git", "show", f":{f}"], capture_output=True)
                dst = os.path.join(tmp, f.replace("/", os.sep))
                os.makedirs(os.path.dirname(dst) or tmp, exist_ok=True)
                with open(dst, "wb") as out:
                    out.write(r.stdout)
                findings += check_file(dst, f, ROOT)
            if print_findings(findings):
                block = True
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    if block:
        print(f"{RED}Commit BỊ CHẶN. Fix lỗi \u2717 rồi commit lại.{RST}")
        print("Bỏ qua khẩn cấp (KHÔNG khuyến khích): git commit --no-verify")
        sys.exit(1)
    print(f"{GRN}\u2713 pre-commit pass{RST}")


# ═══════════════ INIT ═══════════════
HOOK_SHIM = """#!/bin/sh
# Sammis Agent Code — pre-commit shim (do 'python sammis.py init' tạo)
ROOT="$(git rev-parse --show-toplevel)"
if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi
exec "$PY" "$ROOT/sammis.py" precommit
"""

T_PROFILE = '''# Quy chuẩn Sammis Agent Code — khai báo stack riêng dự án
# verify đọc từ đây — không hardcode ở nơi khác.
EXPECTED_PYTHON="3"
# SERVICE_CHECKS="tên|lệnh|chuỗi-kỳ-vọng ;; tên|lệnh|chuỗi"
# Ví dụ Redis+Ollama: SERVICE_CHECKS="redis|redis-cli ping|PONG ;; ollama|curl -s localhost:11434/api/tags|models"
SERVICE_CHECKS=""
REQUIRED_ENV_VARS=""
APP_ENV="staging"
# RISK_OVERRIDE="HIGH"     # người có quyền nâng, hệ thống không tự hạ
AUTORUN_TESTS="0"          # 1 = postagent tự chạy test agent khai
'''

T_PROTECTED = '''# Mỗi dòng một path (tính từ root repo) mà agent CẤM sửa.
# Nguồn: bảng STABLE trong MANIFEST.md. Ba tầng canh: snapshot md5,
# postagent, pre-commit chặn cứng.
# core/bus.py
'''

T_MANIFEST = '''# PROJECT MANIFEST

> Bản đồ tĩnh. Agent đọc TRƯỚC TIÊN. MANIFEST sai làm agent tin sai.

## Thông tin dự án
- **Tên:** [tên] · **Giai đoạn:** [PLANNING|BUILDING|TESTING|PRODUCTION]
- **Một câu:** [dự án làm gì]

## Thành phần STABLE (KHÔNG được sửa — phải có trong .sammis/protected.list)
| File / Module | Trạng thái | Mô tả |
|---|---|---|
| [path] | STABLE | [mô tả] |

## Thành phần IN PROGRESS
| File / Module | Đang làm gì |
|---|---|
| [path] | [mô tả] |

## Thành phần NOT BUILT (CHƯA TỒN TẠI — ĐỪNG IMPORT)
| File / Module | Ghi chú |
|---|---|
| [path] | [khi nào build] |
'''

T_CONTEXT = '''# PROJECT CONTEXT

> Tri thức sâu, đọc SAU MANIFEST.

## 1. Naming convention
## 2. Coding rules (bắt buộc)
- Mọi lỗi xử lý tường minh; cấm except: pass.
## 3. Error-handling contract
## 4. Interface contracts (ĐÃ LOCK — agent chỉ GỌI, không SỬA)
## 5. Known issues
## 6. Quyết định kiến trúc + LÝ DO
'''

T_SPEC = '''# SPEC: [tên task]

> Không spec = không gọi agent. Mục trống là cửa cho agent tự giả định.

## 1. Mục tiêu
## 2. Input
## 3. Output (danh sách file ĐÓNG)
## 4. Logic (từng bước, kể cả nhánh lỗi)
## 5. Dependencies (+ lệnh verify từng cái)
## 6. Không được phép
## 7. Error handling (từng loại lỗi → hành động)
## 8. Acceptance (lệnh chạy thật → kết quả kỳ vọng)
## 9. Ngoài phạm vi
'''

T_CLAUDE = '''# CLAUDE.md — Quy chuẩn Sammis Agent Code

Repo này tuân Quy chuẩn Sammis Agent Code.
**Đọc và tuân thủ toàn bộ `AGENT_RULES.md` tại root trước khi làm bất kỳ việc gì.**
Xong task: ghi `.sammis/runs/run_<timestamp-duy-nhất>.json` khai đủ file đã
tạo/sửa. Repo có trạm gác tự động (pre-commit AST + postagent đối chiếu Git).
'''


def write_if_absent(path, content):
    if os.path.exists(path):
        wr(f"giữ nguyên {path} (đã tồn tại)")
        return
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    ok(f"tạo {path}")


def cmd_init():
    print(f"── Cài Quy chuẩn Sammis Agent Code V5 vào: {ROOT} ──")
    os.makedirs(p_runs(), exist_ok=True)
    os.makedirs("specs", exist_ok=True)

    write_if_absent(p_profile(), T_PROFILE)
    write_if_absent(p_protected(), T_PROTECTED)
    write_if_absent("MANIFEST.md", T_MANIFEST)
    write_if_absent("CONTEXT.md", T_CONTEXT)
    write_if_absent(os.path.join("specs", "_TEMPLATE.md"), T_SPEC)
    write_if_absent("CLAUDE.md", T_CLAUDE)

    # AGENT_RULES.md: chép từ cạnh sammis.py nếu repo chưa có
    here = os.path.dirname(os.path.abspath(__file__))
    src_rules = os.path.join(here, "AGENT_RULES.md")
    if not os.path.exists("AGENT_RULES.md"):
        if os.path.isfile(src_rules) and here != ROOT:
            shutil.copy(src_rules, "AGENT_RULES.md")
            ok("tạo AGENT_RULES.md (chép từ bộ tải về)")
        elif not os.path.isfile(src_rules):
            wr("không thấy AGENT_RULES.md cạnh sammis.py — nhớ tự chép vào repo")

    # Git hook shim — dùng đúng thư mục hooks Git đang trỏ tới
    rc, hookdir = git("rev-parse", "--git-path", "hooks")
    hookdir = hookdir.strip() or os.path.join(".git", "hooks")
    os.makedirs(hookdir, exist_ok=True)
    hook = os.path.join(hookdir, "pre-commit")
    with open(hook, "w", encoding="utf-8", newline="\n") as f:
        f.write(HOOK_SHIM)
    try:
        os.chmod(hook, 0o755)
    except OSError as e:
        wr(f"không chmod được hook ({e}) — trên Windows điều này vô hại")
    ok(f"cài git hook: {hook}")

    # metrics phải được track NGAY TỪ ĐẦU (dữ liệu chưa track có thể mất không dấu vết)
    if not os.path.exists(p_metrics()):
        open(p_metrics(), "a", encoding="utf-8").close()
    gi_lines = [".sammis/runs/*.json", ".sammis/snapshot.md5"]
    existing = ""
    if os.path.isfile(".gitignore"):
        with open(".gitignore", encoding="utf-8") as f:
            existing = f.read()
    with open(".gitignore", "a", encoding="utf-8", newline="\n") as f:
        for line in gi_lines:
            if line not in existing.splitlines():
                f.write(line + "\n")

    print()
    print("── Mức 2 XONG: từ commit tiếp theo, repo đã được canh gác tự động ──")
    print("  Việc còn lại của BẠN (không giao cho agent): điền MANIFEST.md,")
    print("  .sammis/protected.list, CONTEXT.md — rồi: git add -A && git commit")
    print("  Vòng đầy đủ (Mức 3) + cách đo tỉ lệ thật: xem README.md")


# ═══════════════ MAIN ═══════════════
def main():
    global ROOT, SAMMIS
    p = argparse.ArgumentParser(prog="sammis.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    for c in ("init", "preflight", "snapshot", "risk", "postagent", "precommit"):
        sub.add_parser(c)
    pr = sub.add_parser("report")
    pr.add_argument("--md", default=None)
    pl = sub.add_parser("log")
    pl.add_argument("--task", required=True)
    pl.add_argument("--result", required=True, choices=["pass", "fail"])
    pl.add_argument("--codes", default="")
    a = p.parse_args()

    ROOT = repo_root()
    if not ROOT:
        print(f"{RED}\u2717 Đây không phải git repo. Quy chuẩn cần Git làm nguồn sự thật.{RST}")
        print("  → chạy 'git init' trước, rồi chạy lại")
        sys.exit(1)
    os.chdir(ROOT)
    SAMMIS = os.path.join(ROOT, ".sammis")
    os.makedirs(SAMMIS, exist_ok=True)

    {"init": cmd_init, "preflight": cmd_preflight, "snapshot": cmd_snapshot,
     "risk": cmd_risk, "postagent": cmd_postagent, "precommit": cmd_precommit,
     "report": lambda: cmd_report(a.md) if a.cmd == "report" else None,
     "log": lambda: metrics_log(a.task, a.result,
                                [c for c in a.codes.split(",") if c])
     }[a.cmd]()


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        # người dùng pipe qua head/less và đóng sớm — không phải lỗi
        try:
            sys.stdout.close()
        finally:
            sys.exit(0)
