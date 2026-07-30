"""Icon-only tool button."""

from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QToolButton

try:
    from motion_engine.studio.theme import lucide_icon
except ImportError:  # pragma: no cover
    lucide_icon = None  # type: ignore[assignment,misc]


class IconButton(QToolButton):
    """Compact icon button; falls back to text label when icons unavailable."""

    def __init__(
        self,
        icon_name: str,
        *,
        text: str = "",
        tooltip: str = "",
        size: int = 28,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("IconChrome")
        self.setFixedSize(size, size)
        self.setIconSize(QSize(size - 10, size - 10))
        if lucide_icon is not None:
            self.setIcon(lucide_icon(icon_name, size=size - 10))
        else:
            self.setText(text or icon_name[:1].upper())
        if tooltip:
            self.setToolTip(tooltip)
