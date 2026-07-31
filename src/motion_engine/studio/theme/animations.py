"""Motion duration tokens and Qt animation helpers."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget


@dataclass(frozen=True, slots=True)
class StudioMotion:
    """Micro-interaction timings — noticed as polish, never as lag."""

    instant: int = 100
    fast: int = 140
    base: int = 180
    slow: int = 240
    camera: int = 300


def ease_out() -> QEasingCurve:
    return QEasingCurve(QEasingCurve.Type.OutCubic)


def _opacity_effect(widget: QWidget) -> QGraphicsOpacityEffect:
    effect = widget.graphicsEffect()
    if isinstance(effect, QGraphicsOpacityEffect):
        return effect
    created = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(created)
    return created


def fade_in(
    widget: QWidget,
    *,
    duration: int | None = None,
    start: float = 0.0,
    end: float = 1.0,
) -> QPropertyAnimation:
    """Fade a widget in using opacity animation."""
    motion = StudioMotion()
    effect = _opacity_effect(widget)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration if duration is not None else motion.base)
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(ease_out())
    return anim


def fade_out(
    widget: QWidget,
    *,
    duration: int | None = None,
    start: float = 1.0,
    end: float = 0.0,
) -> QPropertyAnimation:
    """Fade a widget out using opacity animation."""
    motion = StudioMotion()
    effect = _opacity_effect(widget)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration if duration is not None else motion.fast)
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(QEasingCurve.Type.InCubic)
    return anim


def slide(
    widget: QWidget,
    start: QPoint,
    end: QPoint,
    *,
    duration: int | None = None,
) -> QPropertyAnimation:
    """Slide a widget between two positions."""
    motion = StudioMotion()
    widget.move(start)
    anim = QPropertyAnimation(widget, b"pos", widget)
    anim.setDuration(duration if duration is not None else motion.base)
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(ease_out())
    return anim
