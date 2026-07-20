"""Minimal top bar - brand, sidebar toggle, open dataset."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget

from motion_engine.studio.icons import icon_app
from motion_engine.studio.theme import DEFAULT_THEME


class CommandBar(QWidget):
    """Clean Apple-style top chrome with only essential navigation."""

    sidebarToggleRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CommandBar")
        self.setFixedHeight(44)
        sp = DEFAULT_THEME.spacing
        layout = QHBoxLayout(self)
        layout.setContentsMargins(sp.md, sp.xs, sp.md, sp.xs)
        layout.setSpacing(sp.sm)

        toggle = QToolButton()
        toggle.setObjectName("IconChrome")
        toggle.setText("☰")
        toggle.setToolTip("Toggle explorer (Ctrl+B)")
        toggle.setShortcut(QKeySequence("Ctrl+B"))
        toggle.clicked.connect(self.sidebarToggleRequested.emit)
        layout.addWidget(toggle)

        mark = QLabel()
        mark.setPixmap(icon_app(24).pixmap(24, 24))
        title = QLabel("AXYX")
        title.setObjectName("BrandTitle")
        layout.addWidget(mark)
        layout.addWidget(title)
        layout.addStretch(1)
