"""Clinical metrics panel."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from motion_engine.studio.format_utils import format_value, tooltip_detail
from motion_engine.studio.theme import DEFAULT_THEME
from motion_engine.studio.widgets.empty_state import EmptyStateWidget


class MetricsPanel(QWidget):
    """List clinical metrics for the active session."""

    def __init__(self, parent: QWidget | None = None, *, show_title: bool = True) -> None:
        super().__init__(parent)
        sp = DEFAULT_THEME.spacing
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, sp.sm, 0, sp.sm)
        layout.setSpacing(sp.sm)
        self._list = QListWidget()
        self._list.setObjectName("MetricsList")
        self._empty = EmptyStateWidget(
            "No metrics",
            "This session has no clinical metrics to display.",
        )
        if show_title:
            from PySide6.QtWidgets import QLabel

            title = QLabel("Clinical Metrics")
            title.setObjectName("SectionLabel")
            layout.addWidget(title)
        layout.addWidget(self._list, stretch=1)
        layout.addWidget(self._empty, stretch=1)
        self._empty.hide()

    def set_metrics(self, metrics: dict[str, Any]) -> None:
        """Populate metric rows."""
        self._list.clear()
        if not metrics:
            self._list.hide()
            self._empty.show()
            return
        self._empty.hide()
        self._list.show()
        for name, value in sorted(metrics.items()):
            item = QListWidgetItem(f"{name}: {format_value(value)}")
            tip = tooltip_detail(value)
            if tip:
                item.setToolTip(tip)
            self._list.addItem(item)
