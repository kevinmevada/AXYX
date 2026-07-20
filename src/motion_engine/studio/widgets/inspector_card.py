"""Collapsible inspector card section."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QToolButton, QVBoxLayout, QWidget

from motion_engine.studio.theme import DEFAULT_THEME


class InspectorCard(QFrame):
    """Glass card with collapse header - used in the right inspector."""

    def __init__(self, title: str, body: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("InspectorCard")
        sp = DEFAULT_THEME.spacing
        layout = QVBoxLayout(self)
        layout.setContentsMargins(sp.sm, sp.sm, sp.sm, sp.sm)
        layout.setSpacing(sp.xs)

        header = QWidget()
        row = QHBoxLayout(header)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(sp.sm)
        self._toggle = QToolButton()
        self._toggle.setObjectName("IconChrome")
        self._toggle.setText("▾")
        self._toggle.setCheckable(True)
        self._toggle.setChecked(True)
        self._toggle.setToolTip("Collapse")
        self._toggle.toggled.connect(self._on_toggle)
        label = QLabel(title)
        label.setObjectName("SectionLabel")
        row.addWidget(self._toggle)
        row.addWidget(label, stretch=1)

        self._body = body
        layout.addWidget(header)
        layout.addWidget(self._body)

    def _on_toggle(self, expanded: bool) -> None:
        self._body.setVisible(expanded)
        self._toggle.setText("▾" if expanded else "▸")
        self._toggle.setToolTip("Collapse" if expanded else "Expand")
