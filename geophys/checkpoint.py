"""Checkpoint & Resume — bài chạy dài ngắt được, chạy tiếp GIỐNG HỆT.

File .npz chứa: digest spec (sha256 — chống resume nhầm bài), rho, u_prev
(warm start CG), n_iter, history JSON. Vì mỗi vòng lặp chỉ phụ thuộc
(rho, u_prev), lưu đủ hai thứ đó là resume tái lập đúng quỹ đạo —
có test DoD-1.4 chứng minh từng bit.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path

import numpy as np

from geophys.spec3d import Spec3D


def spec_digest(spec: Spec3D) -> str:
    """SHA-256 của nội dung spec (ổn định, không phụ thuộc đường dẫn file)."""
    payload = json.dumps(dataclasses.asdict(spec), sort_keys=True,
                         ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def save_checkpoint(path, spec: Spec3D, rho: np.ndarray,
                    u_prev, n_iter: int, history: dict) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        out,
        digest=np.array(spec_digest(spec)),
        rho=rho,
        u_prev=(u_prev if u_prev is not None else np.empty(0)),
        n_iter=np.array(int(n_iter)),
        history_json=np.array(json.dumps(history, ensure_ascii=False)))
    return out


def load_checkpoint(path, spec: Spec3D) -> dict:
    """Nạp checkpoint, ĐỐI CHIẾU digest với spec hiện tại.

    Raises:
        FileNotFoundError: chưa có checkpoint tại path.
        ValueError: checkpoint thuộc bài toán khác (digest lệch).
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(
            f"Không có checkpoint tại {p} — bỏ resume=True để chạy mới")
    data = np.load(p, allow_pickle=False)
    found = str(data["digest"])
    expected = spec_digest(spec)
    if found != expected:
        raise ValueError(
            "Checkpoint thuộc BÀI TOÁN KHÁC — digest checkpoint "
            f"{found[:12]}… ≠ spec hiện tại {expected[:12]}…")
    u_prev = data["u_prev"]
    return {
        "rho": data["rho"],
        "u_prev": (None if u_prev.size == 0 else u_prev),
        "n_iter": int(data["n_iter"]),
        "history": json.loads(str(data["history_json"])),
    }
