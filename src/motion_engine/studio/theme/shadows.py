"""Elevation shadow levels and apply helper."""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget

ELEVATION_LEVELS: dict[int, tuple[int, int, int]] = {
    1: (30, 8, 20),
    2: (36, 10, 28),
    3: (48, 14, 36),
}


def apply_elevation(
    widget: QWidget,
    level: int = 1,
    *,
    color: str | None = None,
    default_shadow: str = "#000000",
) -> None:
    """Apply a soft floating shadow — never heavy clay extrusion."""
    blur, offset, alpha = ELEVATION_LEVELS.get(level, ELEVATION_LEVELS[1])
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, offset)
    q = QColor(color or default_shadow)
    q.setAlpha(alpha)
    effect.setColor(q)
    widget.setGraphicsEffect(effect)
