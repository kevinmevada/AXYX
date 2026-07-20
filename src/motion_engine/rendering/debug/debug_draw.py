"""Immediate-mode debug draw hooks (no-op until a backend binds them)."""

from __future__ import annotations

import logging
from typing import Any, Sequence

logger = logging.getLogger(__name__)


class DebugDraw:
    """Collects debug primitives for optional overlay passes."""

    def __init__(self) -> None:
        self.enabled = False
        self._lines: list[tuple[Sequence[float], Sequence[float], str]] = []

    def clear(self) -> None:
        self._lines.clear()

    def line(
        self,
        start: Sequence[float],
        end: Sequence[float],
        *,
        color: str = "yellow",
    ) -> None:
        if not self.enabled:
            return
        self._lines.append((start, end, color))

    def flush(self, backend: Any) -> None:
        if not self.enabled or not self._lines:
            return
        drawer = getattr(backend, "debug_draw_lines", None)
        if callable(drawer):
            try:
                drawer(self._lines)
            except Exception:
                logger.debug("debug draw flush failed", exc_info=True)
        self.clear()


__all__ = ["DebugDraw"]
