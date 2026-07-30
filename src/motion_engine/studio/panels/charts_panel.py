"""Session metrics chart panel (pyqtgraph) — live Studio dock."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from motion_engine.studio.theme import DEFAULT_THEME

try:
    import pyqtgraph as pg
except ImportError:  # pragma: no cover
    pg = None  # type: ignore[assignment]


class ChartsPanel(QWidget):
    """Plot numeric session metrics; used by the Charts dock."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ChartsPanel")
        self.setAccessibleName("Charts")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            DEFAULT_THEME.spacing.sm,
            DEFAULT_THEME.spacing.sm,
            DEFAULT_THEME.spacing.sm,
            DEFAULT_THEME.spacing.sm,
        )
        self._hint = QLabel("Load a session to view metrics.")
        self._hint.setObjectName("MutedLabel")
        self._hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._hint)
        self._plot = None
        self._playhead = None
        self._last_keys: list[str] = []
        self._last_values: list[float] = []
        if pg is not None:
            pg.setConfigOptions(antialias=True)
            self._plot = pg.PlotWidget()
            self._plot.setBackground(None)
            self._plot.showGrid(x=True, y=True, alpha=0.2)
            self._plot.setLabel("left", "value")
            self._plot.setLabel("bottom", "index")
            self._plot.setAccessibleName("Metrics plot")
            layout.addWidget(self._plot, stretch=1)
            self._hint.hide()

    def set_metrics(self, metrics: dict[str, Any] | None) -> None:
        """Render scalar metrics as a bar-like series."""
        if self._plot is None:
            self._hint.setText("pyqtgraph is not installed.")
            self._hint.show()
            return
        self._plot.clear()
        if not metrics:
            self._hint.setText("No numeric metrics for this session.")
            self._hint.show()
            return
        self._hint.hide()
        keys: list[str] = []
        values: list[float] = []
        for key, raw in metrics.items():
            try:
                values.append(float(raw))
                keys.append(str(key))
            except (TypeError, ValueError):
                continue
        if not values:
            self._hint.setText("No numeric metrics for this session.")
            self._hint.show()
            return
        x = list(range(len(values)))
        bar = pg.BarGraphItem(
            x=x,
            height=values,
            width=0.6,
            brush=DEFAULT_THEME.colors.accent,
        )
        self._plot.addItem(bar)
        axis = self._plot.getAxis("bottom")
        axis.setTicks([[(i, keys[i][:12]) for i in x]])
        self._last_keys = keys
        self._last_values = values

    def set_playhead(self, frame: int) -> None:
        """Show current playback frame as a vertical line when series exist."""
        if self._plot is None:
            return
        if getattr(self, "_playhead", None) is not None:
            self._plot.removeItem(self._playhead)
            self._playhead = None
        # Map frame onto metric index when we only have scalar bars
        values = getattr(self, "_last_values", None)
        if not values:
            return
        x = float(frame % max(len(values), 1))
        pen = pg.mkPen(DEFAULT_THEME.colors.text_muted, width=1)
        self._playhead = pg.InfiniteLine(pos=x, angle=90, pen=pen)
        self._plot.addItem(self._playhead)
