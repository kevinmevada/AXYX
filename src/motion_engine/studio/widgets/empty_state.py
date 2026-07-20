"""Empty-state placeholder used when no data is selected."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from motion_engine.studio.theme import DEFAULT_THEME


class EmptyStateWidget(QFrame):
    """Designed empty state - title, guidance, optional hint."""

    def __init__(
        self,
        title: str = "Nothing selected",
        subtitle: str = "Choose a subject to begin.",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("EmptyState")
        sp = DEFAULT_THEME.spacing
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(sp.xl, sp.xl, sp.xl, sp.xl)
        layout.setSpacing(sp.sm)
        self._title = QLabel(title)
        self._title.setObjectName("EmptyTitle")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle = QLabel(subtitle)
        self._subtitle.setObjectName("EmptySubtitle")
        self._subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle.setWordWrap(True)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)

    def set_messages(self, title: str, subtitle: str) -> None:
        """Update title and subtitle labels."""
        self._title.setText(title)
        self._subtitle.setText(subtitle)
