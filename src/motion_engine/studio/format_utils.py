"""Shared value formatters for inspector / metrics / tooltips."""

from __future__ import annotations

from typing import Any


def format_value(value: Any) -> str:
    """Summarize ``value`` for display; never dump raw Python reprs."""
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        return f"{value:.4g}"
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace") or "-"
    if isinstance(value, dict):
        if not value:
            return "-"
        return "1 field" if len(value) == 1 else f"{len(value)} fields"
    if isinstance(value, (list, tuple)):
        if not value:
            return "-"
        if len(value) > 3 or any(
            isinstance(v, (bytes, list, tuple, dict)) for v in value
        ):
            return "1 value" if len(value) == 1 else f"{len(value)} values"
        return ", ".join(format_scalar(v) for v in value)
    text = str(value)
    return text if len(text) < 60 else text[:57] + "…"


def format_scalar(value: Any) -> str:
    """Format a single scalar for inline lists."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def tooltip_detail(value: Any) -> str | None:
    """Return a full-detail tooltip when the summary was truncated."""
    full = str(value)
    if len(full) > 60 or isinstance(value, (dict, list, tuple, bytes)):
        return full
    return None
