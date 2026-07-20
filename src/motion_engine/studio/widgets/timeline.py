"""Timeline / frame scrubber widget."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSlider, QWidget

from motion_engine.studio.models.playback_model import PlaybackModel
from motion_engine.studio.theme import DEFAULT_THEME


class TimelineWidget(QWidget):
    """Frame slider with current/total labels and live scrub preview."""

    frameSeeked = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        sp = DEFAULT_THEME.spacing
        layout = QHBoxLayout(self)
        layout.setContentsMargins(sp.sm, 0, sp.sm, sp.sm)
        layout.setSpacing(sp.sm)

        self._label = QLabel("Frame 0 / 0")
        self._label.setObjectName("MutedLabel")
        self._label.setMinimumWidth(110)
        self._preview = QLabel("")
        self._preview.setObjectName("EyebrowLabel")
        self._preview.hide()
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setObjectName("TimelineScrubber")
        self._slider.setMinimum(0)
        self._slider.setMaximum(0)
        self._slider.setToolTip("Scrub timeline")
        self._slider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._slider.sliderPressed.connect(self._on_press)
        self._slider.sliderMoved.connect(self._on_moved)
        self._slider.sliderReleased.connect(self._on_release)
        self._slider.valueChanged.connect(self._on_slider)

        layout.addWidget(self._label)
        layout.addWidget(self._preview)
        layout.addWidget(self._slider, stretch=1)
        self._updating = False
        self._scrubbing = False

    def sync_from_model(self, model: PlaybackModel) -> None:
        """Sync slider range and value from playback state."""
        if self._scrubbing:
            return
        self._updating = True
        maximum = max(0, model.frame_count - 1)
        self._slider.setMaximum(maximum)
        self._slider.setValue(min(model.current_frame, maximum))
        self._label.setText(f"Frame {model.current_frame} / {maximum}")
        self._updating = False

    def _on_press(self) -> None:
        self._scrubbing = True
        self._preview.show()
        self._preview.setText(f"→ {self._slider.value()}")

    def _on_moved(self, value: int) -> None:
        self._preview.setText(f"→ {value}")
        self._label.setText(f"Frame {value} / {self._slider.maximum()}")

    def _on_release(self) -> None:
        self._scrubbing = False
        self._preview.hide()
        self.frameSeeked.emit(int(self._slider.value()))

    def _on_slider(self, value: int) -> None:
        if self._updating or self._scrubbing:
            return
        self.frameSeeked.emit(int(value))
