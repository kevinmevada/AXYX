"""Floating glass panel wrapper — margin + drop shadow for depth."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget

from motion_engine.studio.theme import apply_elevation


class FloatingPanel(QFrame):
    """Wrap content in a styled frame with soft elevation."""

    def __init__(
        self,
        content: QWidget,
        *,
        object_name: str = "FloatingPanel",
        level: int = 2,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName(object_name)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(content)
        apply_elevation(self, level=level)
