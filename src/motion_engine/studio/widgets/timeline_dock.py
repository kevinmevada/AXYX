"""Premium transport — elevated play/pause, hairline scrub, pill speed."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QKeySequence, QPalette
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
    ICON_MD,
    icon_next,
    icon_prev,
    icon_stop,
)
from motion_engine.studio.models.playback_model import PlaybackModel, PlaybackState
from motion_engine.studio.theme import DEFAULT_THEME
from motion_engine.studio.widgets.play_pause_button import PlayPauseButton


class TimelineDock(QWidget):
    """Bottom transport: timecode · controls · rounded scrub track."""

    playClicked = Signal()
    pauseClicked = Signal()
    stopClicked = Signal()
    previousClicked = Signal()
    nextClicked = Signal()
    speedChanged = Signal(float)
    loopChanged = Signal(bool)
    frameSeeked = Signal(int)
    resetCameraClicked = Signal()
    playPauseToggled = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TimelineDock")
        self.setFixedHeight(104)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        bg = QColor(DEFAULT_THEME.colors.background)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, bg)
        pal.setColor(QPalette.ColorRole.Base, bg)
        self.setPalette(pal)

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 12, 32, 16)
        root.setSpacing(12)

        transport = QHBoxLayout()
        transport.setSpacing(0)
        transport.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._frame = QLabel("FRAME 000/0  ·  00:00.00")
        self._frame.setObjectName("FrameLabel")
        self._frame.setFixedHeight(52)
        self._frame.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._timecode = QLabel("")
        self._timecode.setObjectName("TimecodeLabel")
        self._timecode.hide()

        cluster = QHBoxLayout()
        cluster.setContentsMargins(0, 0, 0, 0)
        cluster.setSpacing(16)
        cluster.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._prev = self._bare("Previous (←)", icon_prev(ICON_MD), "Left")
        self._prev.setAccessibleName("Previous frame")
        self._prev.clicked.connect(self.previousClicked.emit)

        self._play_pause = PlayPauseButton()
        self._play_pause.toggledPlayback.connect(self._on_play_pause)

        self._stop = self._bare("Stop (Home)", icon_stop(ICON_MD, danger=True), "Home")
        self._stop.setObjectName("StopTransportButton")
        self._stop.setAccessibleName("Stop")
        self._stop.clicked.connect(self.stopClicked.emit)

        self._next = self._bare("Next (→)", icon_next(ICON_MD), "Right")
        self._next.setAccessibleName("Next frame")
        self._next.clicked.connect(self.nextClicked.emit)

        for w in (self._prev, self._play_pause, self._stop, self._next):
            cluster.addWidget(w, 0, Qt.AlignmentFlag.AlignVCenter)

        self._speed = QComboBox()
        self._speed.setObjectName("SpeedPill")
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
        self._speed.setFixedHeight(32)
        self._speed.setMinimumWidth(72)
        self._speed.setToolTip("Playback speed")
        self._speed.currentIndexChanged.connect(self._on_speed_changed)

        self._loop = QToolButton()
        self._loop.setObjectName("LoopButton")
        self._loop.setText("Loop")
        self._loop.setCheckable(True)
        self._loop.setChecked(True)
        self._loop.setFixedHeight(32)
        self._loop.setCursor(Qt.CursorShape.PointingHandCursor)
        self._loop.setToolTip("Loop playback")
        self._loop.toggled.connect(self.loopChanged.emit)

        transport.addWidget(self._frame, 0, Qt.AlignmentFlag.AlignVCenter)
        transport.addStretch(1)
        transport.addLayout(cluster)
        transport.addStretch(1)
        transport.addWidget(self._speed, 0, Qt.AlignmentFlag.AlignVCenter)
        transport.addSpacing(8)
        transport.addWidget(self._loop, 0, Qt.AlignmentFlag.AlignVCenter)

        scrub = QHBoxLayout()
        scrub.setContentsMargins(0, 0, 0, 0)
        scrub.setSpacing(0)
        self._preview = QLabel("")
        self._preview.setObjectName("EyebrowLabel")
        self._preview.hide()
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setObjectName("TimelineScrubber")
        self._slider.setAccessibleName("Timeline scrubber")
        self._slider.setMinimum(0)
        self._slider.setMaximum(0)
        self._slider.setFixedHeight(20)
        self._slider.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._slider.setCursor(Qt.CursorShape.PointingHandCursor)
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
        self._playing = False
        self._fps = 100.0
        self.playback_toolbar = self
        self.timeline = self

    def _on_play_pause(self) -> None:
        self.playPauseToggled.emit()

    def toggle_play_pause(self) -> None:
        self.playPauseToggled.emit()

    @staticmethod
    def _bare(tip: str, icon, shortcut: str) -> QToolButton:
        btn = QToolButton()
        btn.setObjectName("TransportButton")
        btn.setIcon(icon)
        btn.setToolTip(tip)
        btn.setFixedSize(48, 48)
        btn.setIconSize(QSize(20, 20))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setAutoRaise(True)
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        btn.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        if shortcut:
            btn.setShortcut(QKeySequence(shortcut))
        return btn

    def sync_from_model(self, model: PlaybackModel) -> None:
        if self._scrubbing:
            return
        self._updating = True
        self._fps = float(model.fps) if model.fps else 100.0
        maximum = max(0, model.frame_count - 1)
        self._slider.setMaximum(maximum)
        self._slider.setValue(min(model.current_frame, maximum))
        total = max(model.frame_count, 0)
        self._frame.setText(
            f"FRAME {model.current_frame:03d}/{total}  ·  {_fmt(model.current_time_sec)}"
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
        self._playing = playing
        self._play_pause.set_playing(playing)
        self._play_pause.set_playback_enabled(model.frame_count > 0)
        self._updating = False

    def _on_speed_changed(self, index: int) -> None:
        value = self._speed.itemData(index)
        if value is not None:
            self.speedChanged.emit(float(value))

    def _on_press(self) -> None:
        self._scrubbing = True
        self._preview.show()
        self._update_frame_label(self._slider.value())

    def _on_moved(self, value: int) -> None:
        self._update_frame_label(value)
        self._preview.setText(f"→ {value}")

    def _on_release(self) -> None:
        self._scrubbing = False
        self._preview.hide()
        self.frameSeeked.emit(int(self._slider.value()))

    def _on_slider(self, value: int) -> None:
        if self._updating:
            return
        if self._scrubbing:
            self._update_frame_label(value)
            return
        self.frameSeeked.emit(int(value))

    def _update_frame_label(self, frame: int) -> None:
        total = max(self._slider.maximum() + 1, 0)
        t = frame / self._fps if self._fps > 0 else 0.0
        self._frame.setText(f"FRAME {frame:03d}/{total}  ·  {_fmt(t)}")


def _fmt(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    minutes = int(seconds // 60)
    rem = seconds - minutes * 60
    return f"{minutes:02d}:{rem:05.2f}"
