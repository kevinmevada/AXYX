"""Inline error banner for non-blocking failures."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from motion_engine.studio.theme import DEFAULT_THEME


class ErrorBanner(QFrame):
    """Compact dismissible error strip (prefer over modal for soft failures)."""

    dismissed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ErrorBanner")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QHBoxLayout(self)
        sp = DEFAULT_THEME.spacing
        layout.setContentsMargins(sp.md, sp.sm, sp.md, sp.sm)
        layout.setSpacing(sp.sm)
        self._text = QLabel()
        self._text.setObjectName("ErrorBannerText")
        self._text.setWordWrap(True)
        dismiss = QPushButton("Dismiss")
        dismiss.setObjectName("GhostButton")
        dismiss.clicked.connect(self.hide)
        dismiss.clicked.connect(self.dismissed.emit)
        layout.addWidget(self._text, stretch=1)
        layout.addWidget(dismiss)
        self.hide()

    def show_error(self, title: str, message: str) -> None:
        """Show ``title`` + ``message`` and raise the banner."""
        self._text.setText(f"{title}: {message}")
        self.show()
        self.raise_()
