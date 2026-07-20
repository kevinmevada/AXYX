"""Playback toolbar for AXYX."""

from __future__ import annotations

from PySide6.QtGui import QKeySequence
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QWidget,
)

from motion_engine.studio.icons import (
    ICON_MD,
    icon_next,
    icon_pause,
    icon_play,
    icon_prev,
    icon_stop,
)
from motion_engine.studio.models.playback_model import PlaybackModel, PlaybackState
from motion_engine.studio.theme import DEFAULT_THEME


class PlaybackToolbar(QWidget):
    """Transport controls: play/pause/stop, step, speed, loop."""

    playClicked = Signal()
    pauseClicked = Signal()
    stopClicked = Signal()
    previousClicked = Signal()
    nextClicked = Signal()
    speedChanged = Signal(float)
    loopChanged = Signal(bool)
    openViewerClicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        sp = DEFAULT_THEME.spacing
        layout = QHBoxLayout(self)
        layout.setContentsMargins(sp.sm, sp.sm, sp.sm, sp.sm)
        layout.setSpacing(sp.sm)

        self._play = self._transport("Play (Space)", icon_play(ICON_MD), "Space")
        self._play.clicked.connect(self.playClicked.emit)
        self._pause = self._transport("Pause (Space)", icon_pause(ICON_MD), "")
        self._pause.clicked.connect(self.pauseClicked.emit)
        self._stop = self._transport("Stop (Home)", icon_stop(ICON_MD), "Home")
        self._stop.clicked.connect(self.stopClicked.emit)
        self._prev = self._transport("Previous frame (Left)", icon_prev(ICON_MD), "Left")
        self._prev.clicked.connect(self.previousClicked.emit)
        self._next = self._transport("Next frame (Right)", icon_next(ICON_MD), "Right")
        self._next.clicked.connect(self.nextClicked.emit)

        self._speed = QDoubleSpinBox()
        self._speed.setRange(0.1, 4.0)
        self._speed.setSingleStep(0.1)
        self._speed.setValue(1.0)
        self._speed.setSuffix("Ã-")
        self._speed.setToolTip("Playback speed")
        self._speed.valueChanged.connect(self.speedChanged.emit)

        self._loop = QCheckBox("Loop")
        self._loop.setChecked(True)
        self._loop.setToolTip("Loop when reaching the last frame")
        self._loop.toggled.connect(self.loopChanged.emit)

        self._time = QLabel("00:00.00 / 00:00.00")
        self._time.setObjectName("MutedLabel")

        self._viewer = QToolButton()
        self._viewer.setText("Reset Camera")
        self._viewer.setToolTip("Reset the embedded motion viewport camera (R)")
        self._viewer.clicked.connect(self.openViewerClicked.emit)

        for widget in (
            self._play,
            self._pause,
            self._stop,
            self._prev,
            self._next,
            QLabel("Speed"),
            self._speed,
            self._loop,
            self._time,
        ):
            layout.addWidget(widget)
        layout.addStretch(1)
        layout.addWidget(self._viewer)

    @staticmethod
    def _transport(tip: str, icon, shortcut: str) -> QToolButton:
        btn = QToolButton()
        btn.setObjectName("TransportButton")
        btn.setIcon(icon)
        btn.setToolTip(tip)
        btn.setAutoRaise(False)
        if shortcut:
            btn.setShortcut(QKeySequence(shortcut))
        return btn

    def sync_from_model(self, model: PlaybackModel) -> None:
        """Update labels / checked state from the playback model."""
        self._speed.blockSignals(True)
        self._loop.blockSignals(True)
        self._speed.setValue(model.speed)
        self._loop.setChecked(model.loop)
        self._speed.blockSignals(False)
        self._loop.blockSignals(False)
        self._time.setText(
            f"{_fmt_time(model.current_time_sec)} / {_fmt_time(model.duration_sec)}  |  "
            f"{model.state.value}"
        )
        playing = model.state == PlaybackState.PLAYING
        self._play.setEnabled(not playing and model.frame_count > 0)
        self._pause.setEnabled(playing)
        self._pause.setCheckable(True)
        self._pause.setChecked(playing)


def _fmt_time(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    minutes = int(seconds // 60)
    rem = seconds - minutes * 60
    return f"{minutes:02d}:{rem:05.2f}"
