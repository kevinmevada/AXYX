"""Key/value metadata panel."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QFormLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from motion_engine.studio.format_utils import format_value, tooltip_detail
from motion_engine.studio.theme import DEFAULT_THEME
from motion_engine.studio.widgets.empty_state import EmptyStateWidget


class MetadataPanel(QWidget):
    """Scrollable key/value form for session or subject metadata."""

    def __init__(self, title: str = "Metadata", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        sp = DEFAULT_THEME.spacing
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(sp.sm)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._host = QWidget()
        self._form = QFormLayout(self._host)
        self._form.setContentsMargins(sp.xs, sp.sm, sp.xs, sp.sm)
        self._form.setHorizontalSpacing(sp.lg)
        self._form.setVerticalSpacing(sp.sm + 2)
        scroll.setWidget(self._host)
        self._empty = EmptyStateWidget(
            "No fields",
            "Select a session to inspect clinical metadata.",
        )
        if title:
            heading = QLabel(title)
            heading.setObjectName("SectionLabel")
            root.addWidget(heading)
        root.addWidget(scroll, stretch=1)
        root.addWidget(self._empty, stretch=1)
        self._empty.hide()

    def set_fields(self, fields: dict[str, Any]) -> None:
        """Replace form rows with ``fields``."""
        while self._form.rowCount():
            self._form.removeRow(0)
        if not fields:
            self._host.hide()
            self._empty.show()
            return
        self._empty.hide()
        self._host.show()
        for key, value in fields.items():
            label = QLabel(str(key))
            label.setObjectName("MutedLabel")
            value_label = QLabel(format_value(value))
            value_label.setWordWrap(True)
            tip = tooltip_detail(value)
            if tip:
                value_label.setToolTip(tip)
            self._form.addRow(label, value_label)
