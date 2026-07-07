"""Lỗi có cấu trúc, máy đọc được — theo CONTEXT.md mục 3."""

from __future__ import annotations


class SpecError(Exception):
    """Lỗi spec.json: nêu đúng tên trường, lý do, gợi ý sửa.

    Thuộc tính máy-đọc-được: field / reason / hint.
    """

    def __init__(self, field: str, reason: str, hint: str = "") -> None:
        self.field = field
        self.reason = reason
        self.hint = hint
        msg = f"[spec:{field}] {reason}"
        if hint:
            msg = f"{msg} — gợi ý: {hint}"
        super().__init__(msg)
