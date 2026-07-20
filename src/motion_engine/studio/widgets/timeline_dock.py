"""Compact Apple Music / Final Cut-style timeline dock."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QSlider,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from motion_engine.studio.icons import (
    ICON_SM,
    icon_next,
    icon_pause,
    icon_play,
    icon_prev,
    icon_stop,
)
from motion_engine.studio.models.playback_model import PlaybackModel, PlaybackState
from motion_engine.studio.theme import DEFAULT_THEME


class TimelineDock(QWidget):
    """Bottom dock: compact transport + scrubber + timecode."""

    playClicked = Signal()
    pauseClicked = Signal()
    stopClicked = Signal()
    previousClicked = Signal()
    nextClicked = Signal()
    speedChanged = Signal(float)
    loopChanged = Signal(bool)
    frameSeeked = Signal(int)
    resetCameraClicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TimelineDock")
        self.setFixedHeight(72)
        sp = DEFAULT_THEME.spacing

        root = QVBoxLayout(self)
        root.setContentsMargins(sp.md, sp.sm, sp.md, sp.sm)
        root.setSpacing(sp.xs)

        transport = QHBoxLayout()
        transport.setSpacing(sp.xs)

        self._frame = QLabel("0 / 0")
        self._frame.setObjectName("FrameLabel")
        self._timecode = QLabel("00:00.00")
        self._timecode.setObjectName("TimecodeLabel")

        self._play = self._btn("Play (Space)", icon_play(ICON_SM), "Space")
        self._play.clicked.connect(self.playClicked.emit)
        self._pause = self._btn("Pause", icon_pause(ICON_SM), "")
        self._pause.setCheckable(True)
        self._pause.clicked.connect(self.pauseClicked.emit)
        self._stop = self._btn("Stop (Home)", icon_stop(ICON_SM), "Home")
        self._stop.clicked.connect(self.stopClicked.emit)
        self._prev = self._btn("Previous (←)", icon_prev(ICON_SM), "Left")
        self._prev.clicked.connect(self.previousClicked.emit)
        self._next = self._btn("Next (→)", icon_next(ICON_SM), "Right")
        self._next.clicked.connect(self.nextClicked.emit)

        self._speed = QComboBox()
        self._speed.setObjectName("CompactSpeed")
        for label, value in (
            ("0.25×", 0.25),
            ("0.5×", 0.5),
            ("1×", 1.0),
            ("1.5×", 1.5),
            ("2×", 2.0),
            ("4×", 4.0),
        ):
            self._speed.addItem(label, value)
        self._speed.setCurrentIndex(2)
        self._speed.setFixedSize(72, 30)
        self._speed.setToolTip("Playback speed")
        self._speed.currentIndexChanged.connect(self._on_speed_changed)

        self._loop = QToolButton()
        self._loop.setObjectName("LoopButton")
        self._loop.setText("Loop")
        self._loop.setCheckable(True)
        self._loop.setChecked(True)
        self._loop.setFixedHeight(28)
        self._loop.setToolTip("Loop playback")
        self._loop.toggled.connect(self.loopChanged.emit)

        transport.addWidget(self._frame)
        transport.addWidget(self._timecode)
        transport.addStretch(1)
        for w in (self._prev, self._play, self._pause, self._stop, self._next):
            transport.addWidget(w)
        transport.addStretch(1)
        transport.addWidget(self._speed)
        transport.addWidget(self._loop)

        scrub = QHBoxLayout()
        scrub.setSpacing(sp.sm)
        self._preview = QLabel("")
        self._preview.setObjectName("EyebrowLabel")
        self._preview.hide()
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setObjectName("TimelineScrubber")
        self._slider.setMinimum(0)
        self._slider.setMaximum(0)
        self._slider.setFixedHeight(18)
        self._slider.setToolTip("Scrub timeline")
        self._slider.sliderPressed.connect(self._on_press)
        self._slider.sliderMoved.connect(self._on_moved)
        self._slider.sliderReleased.connect(self._on_release)
        self._slider.valueChanged.connect(self._on_slider)
        scrub.addWidget(self._preview)
        scrub.addWidget(self._slider, stretch=1)

        root.addLayout(transport)
        root.addLayout(scrub)

        self._updating = False
        self._scrubbing = False
        self.playback_toolbar = self
        self.timeline = self

    @staticmethod
    def _btn(tip: str, icon, shortcut: str) -> QToolButton:
        from PySide6.QtCore import QSize

        btn = QToolButton()
        btn.setObjectName("TransportButton")
        btn.setIcon(icon)
        btn.setToolTip(tip)
        btn.setFixedSize(28, 28)
        btn.setIconSize(QSize(16, 16))
        if shortcut:
            btn.setShortcut(QKeySequence(shortcut))
        return btn

    def sync_from_model(self, model: PlaybackModel) -> None:
        if self._scrubbing:
            return
        self._updating = True
        maximum = max(0, model.frame_count - 1)
        self._slider.setMaximum(maximum)
        self._slider.setValue(min(model.current_frame, maximum))
        self._frame.setText(f"{model.current_frame} / {maximum}")
        self._timecode.setText(
            f"{_fmt(model.current_time_sec)} / {_fmt(model.duration_sec)}"
        )
        self._speed.blockSignals(True)
        self._loop.blockSignals(True)
        speed_index = self._speed.findData(float(model.speed))
        if speed_index < 0:
            speed_index = self._speed.findData(1.0)
        self._speed.setCurrentIndex(speed_index)
        self._loop.setChecked(model.loop)
        self._speed.blockSignals(False)
        self._loop.blockSignals(False)
        playing = model.state == PlaybackState.PLAYING
        self._play.setEnabled(not playing and model.frame_count > 0)
        self._pause.setEnabled(playing)
        self._pause.setChecked(playing)
        self._updating = False

    def _on_speed_changed(self, index: int) -> None:
        value = self._speed.itemData(index)
        if value is not None:
            self.speedChanged.emit(float(value))

    def _on_press(self) -> None:
        self._scrubbing = True
        self._preview.show()
        self._preview.setText(f"→ {self._slider.value()}")

    def _on_moved(self, value: int) -> None:
        self._preview.setText(f"→ {value}")
        self._frame.setText(f"{value} / {self._slider.maximum()}")

    def _on_release(self) -> None:
        self._scrubbing = False
        self._preview.hide()
        self.frameSeeked.emit(int(self._slider.value()))

    def _on_slider(self, value: int) -> None:
        if self._updating or self._scrubbing:
            return
        self.frameSeeked.emit(int(value))


def _fmt(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    minutes = int(seconds // 60)
    rem = seconds - minutes * 60
    return f"{minutes:02d}:{rem:05.2f}"
