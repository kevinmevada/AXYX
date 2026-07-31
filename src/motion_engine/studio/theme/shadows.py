"""Soft elevation via drop shadows (GPU-composited Qt effects)."""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget

# blur, y-offset, alpha (0–255)
ELEVATION_LEVELS: dict[int, tuple[int, int, int]] = {
    1: (12, 2, 28),
    2: (20, 4, 36),
    3: (28, 6, 44),
}


def apply_elevation(
    widget: QWidget,
    level: int = 1,
    *,
    color: str | None = None,
    default_shadow: str = "rgba(28, 30, 35, 0.14)",
) -> None:
    """Apply a soft drop shadow. Safe to call repeatedly."""
    blur, y_off, alpha = ELEVATION_LEVELS.get(level, ELEVATION_LEVELS[1])
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, y_off)
    base = QColor(color or default_shadow)
    if base.alpha() == 255 and color is None:
        base.setAlpha(alpha)
    effect.setColor(base)
    widget.setGraphicsEffect(effect)
