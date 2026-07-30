"""Ephemeral toast notification."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QWidget

from motion_engine.studio.theme import DEFAULT_THEME, fade_in, fade_out


def show_toast(
    parent: QWidget,
    message: str,
    *,
    duration_ms: int = 2400,
) -> QLabel:
    """Show a fading toast anchored to the bottom-center of ``parent``."""
    toast = QLabel(message, parent)
    toast.setObjectName("ToastLabel")
    toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
    toast.setWordWrap(True)
    toast.adjustSize()
    sp = DEFAULT_THEME.spacing
    margin = sp.lg
    x = max(margin, (parent.width() - toast.width()) // 2)
    y = max(margin, parent.height() - toast.height() - margin * 2)
    toast.move(x, y)
    toast.show()
    fade_in(toast).start()
    QTimer.singleShot(
        duration_ms,
        lambda: _dismiss(toast),
    )
    return toast


def _dismiss(toast: QLabel) -> None:
    anim = fade_out(toast)
    anim.finished.connect(toast.deleteLater)
    anim.start()
