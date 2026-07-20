"""Right inspector - collapsible glass cards."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget

from motion_engine.studio.theme import DEFAULT_THEME
from motion_engine.studio.widgets.inspector_card import InspectorCard
from motion_engine.studio.widgets.metadata_panel import MetadataPanel
from motion_engine.studio.widgets.metrics_panel import MetricsPanel


class InspectorPanel(QFrame):
    """Session / Clinical / Metrics / Dataset cards."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("InspectorPanel")
        self.setMinimumWidth(260)
        self.setMaximumWidth(400)
        sp = DEFAULT_THEME.spacing

        root = QVBoxLayout(self)
        root.setContentsMargins(sp.md, sp.md, sp.md, sp.md)
        root.setSpacing(sp.md)

        heading = QLabel("Inspector")
        heading.setObjectName("BrandTitle")
        root.addWidget(heading)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        host = QWidget()
        self._cards = QVBoxLayout(host)
        self._cards.setContentsMargins(0, 0, 0, 0)
        self._cards.setSpacing(sp.sm)

        self.clinical = MetadataPanel("")
        self.metrics = MetricsPanel(show_title=False)
        self.dataset = MetadataPanel("")
        self.playback = MetadataPanel("")

        self._cards.addWidget(InspectorCard("Clinical", self.clinical))
        self._cards.addWidget(InspectorCard("Metrics", self.metrics))
        self._cards.addWidget(InspectorCard("Dataset", self.dataset))
        self._cards.addWidget(InspectorCard("Motion", self.playback))
        # Soft spacer - cards breathe
        self._cards.addStretch(1)
        scroll.setWidget(host)
        root.addWidget(scroll, stretch=1)

        # Compat: some code still references .tabs
        self.tabs = self

    def set_clinical(self, fields: dict[str, Any]) -> None:
        self.clinical.set_fields(fields)

    def set_metrics(self, metrics: dict[str, Any]) -> None:
        self.metrics.set_metrics(metrics)

    def set_dataset(self, fields: dict[str, Any]) -> None:
        self.dataset.set_fields(fields)

    def set_playback(self, fields: dict[str, Any]) -> None:
        self.playback.set_fields(fields)
