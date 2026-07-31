"""Premium play/pause toggle with geometric path morph."""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPointF,
    QPropertyAnimation,
    QRectF,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor, QPainter, QPainterPath, QRadialGradient
from PySide6.QtWidgets import QAbstractButton, QGraphicsDropShadowEffect, QWidget

from motion_engine.studio.theme import DEFAULT_THEME

# Shared 24×24 optical box — play triangle ↔ pause bars, same footprint.
_PLAY = (
    (7.0, 4.0),
    (13.5, 8.25),
    (13.5, 15.75),
    (7.0, 20.0),
    (13.5, 8.25),
    (20.0, 12.0),
    (20.0, 12.0),
    (13.5, 15.75),
)
_PAUSE = (
    (8.0, 5.0),
    (11.0, 5.0),
    (11.0, 19.0),
    (8.0, 19.0),
    (13.0, 5.0),
    (16.0, 5.0),
    (16.0, 19.0),
    (13.0, 19.0),
)

_SIZE = 52
_HOVER_SCALE = 1.04
_PRESS_SCALE = 0.97


def _spring_curve() -> QEasingCurve:
    curve = QEasingCurve(QEasingCurve.Type.OutBack)
    curve.setOvershoot(1.35)
    return curve


def _ease_out() -> QEasingCurve:
    return QEasingCurve(QEasingCurve.Type.OutCubic)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


class PlayPauseButton(QAbstractButton):
    """52px elevated accent circle — morphs play ↔ pause with press/hover scale."""

    toggledPlayback = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PlayPauseButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCheckable(False)
        self.setFixedSize(_SIZE, _SIZE)
        self.setToolTip("Play (Space)")
        self.setAccessibleName("Play")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._playing = False
        self._enabled_playback = True
        self._morph = 0.0
        self._scale = 1.0
        self._press_armed = False
        self._hovered = False
        self._morph_token = 0

        self._morph_anim = QPropertyAnimation(self, b"morph", self)
        self._morph_anim.setDuration(180)
        self._morph_anim.setEasingCurve(_spring_curve())

        self._scale_anim = QPropertyAnimation(self, b"scale", self)
        self._scale_anim.setDuration(120)
        self._scale_anim.setEasingCurve(_ease_out())

        self._apply_shadow(resting=True)
        self.clicked.connect(self._on_clicked)
        self.setEnabled(False)

    def _apply_shadow(self, *, resting: bool) -> None:
        effect = QGraphicsDropShadowEffect(self)
        effect.setBlurRadius(18 if resting else 24)
        effect.setOffset(0, 3 if resting else 5)
        c = QColor(DEFAULT_THEME.colors.accent)
        c.setAlpha(55 if resting else 80)
        effect.setColor(c)
        self.setGraphicsEffect(effect)

    def get_morph(self) -> float:
        return self._morph

    def set_morph(self, value: float) -> None:
        self._morph = max(0.0, min(1.0, float(value)))
        self.update()

    morph = Property(float, get_morph, set_morph)

    def get_scale(self) -> float:
        return self._scale

    def set_scale(self, value: float) -> None:
        self._scale = float(value)
        self.update()

    scale = Property(float, get_scale, set_scale)

    @property
    def playing(self) -> bool:
        return self._playing

    def set_playing(self, playing: bool) -> None:
        playing = bool(playing)
        target = 1.0 if playing else 0.0
        if self._playing == playing:
            self._refresh_chrome()
            return
        self._playing = playing
        self._refresh_chrome()

        delay = 80 if self._press_armed else 0
        self._press_armed = False
        self._morph_token += 1
        token = self._morph_token

        def _start() -> None:
            if token != self._morph_token:
                return
            self._morph_anim.stop()
            self._morph_anim.setStartValue(self._morph)
            self._morph_anim.setEndValue(target)
            self._morph_anim.start()

        if delay:
            QTimer.singleShot(delay, _start)
        else:
            _start()

    def set_playback_enabled(self, enabled: bool) -> None:
        self._enabled_playback = bool(enabled)
        self.setEnabled(self._enabled_playback)
        self.update()

    def _refresh_chrome(self) -> None:
        if self._playing:
            self.setToolTip("Pause (Space)")
            self.setAccessibleName("Pause")
        else:
            self.setToolTip("Play (Space)")
            self.setAccessibleName("Play")

    def _animate_scale(self, target: float, duration: int = 120) -> None:
        self._scale_anim.stop()
        self._scale_anim.setDuration(duration)
        self._scale_anim.setEasingCurve(_ease_out())
        self._scale_anim.setStartValue(self._scale)
        self._scale_anim.setEndValue(target)
        self._scale_anim.start()

    def enterEvent(self, event) -> None:  # noqa: N802
        self._hovered = True
        if self.isEnabled() and not self.isDown():
            self._animate_scale(_HOVER_SCALE, 140)
            self._apply_shadow(resting=False)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hovered = False
        self._press_armed = False
        if not self.isDown():
            self._animate_scale(1.0, 140)
            self._apply_shadow(resting=True)
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            self._press_armed = True
            self._animate_scale(_PRESS_SCALE, 80)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            target = _HOVER_SCALE if self._hovered else 1.0
            self._animate_scale(target, 160)
            self._apply_shadow(resting=not self._hovered)
        super().mouseReleaseEvent(event)

    def _on_clicked(self) -> None:
        if not self._enabled_playback:
            return
        self.toggledPlayback.emit()

    def paintEvent(self, _event) -> None:  # noqa: N802
        c = DEFAULT_THEME.colors
        accent = QColor(c.accent)
        hover = QColor(c.accent_hover)
        pressed = QColor(c.accent_pressed)
        on_accent = QColor(c.text_on_accent)
        disabled = QColor(c.text_disabled)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w * 0.5, h * 0.5
        scale = max(0.85, self._scale)
        radius = min(w, h) * 0.5 * scale - 0.5

        painter.setPen(Qt.PenStyle.NoPen)
        # Anodized-metal fill: deep violet core → lighter rim (UI chrome, not viewport glow).
        metal = QRadialGradient(cx - radius * 0.28, cy - radius * 0.32, radius * 1.15)
        if not self.isEnabled():
            metal.setColorAt(0.0, disabled.lighter(120))
            metal.setColorAt(1.0, disabled)
        elif self.isDown():
            metal.setColorAt(0.0, QColor(c.accent_hover))
            metal.setColorAt(0.55, pressed)
            metal.setColorAt(1.0, pressed.darker(110))
        elif self._hovered:
            metal.setColorAt(0.0, hover.lighter(115))
            metal.setColorAt(0.45, hover)
            metal.setColorAt(1.0, accent)
        else:
            metal.setColorAt(0.0, QColor(c.accent_hover))
            metal.setColorAt(0.4, accent)
            metal.setColorAt(1.0, pressed)
        painter.setBrush(metal)
        painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        clip = QPainterPath()
        clip.addEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))
        painter.setClipPath(clip)
        painter.setBrush(on_accent if self.isEnabled() else QColor(c.surface))

        box = 24.0
        icon = radius * 2.0 * (16.0 / 24.0)
        ox = cx - icon * 0.5
        oy = cy - icon * 0.5
        s = icon / box
        t = self._morph

        for i in (0, 4):
            path = QPainterPath()
            for j, idx in enumerate(range(i, i + 4)):
                x = _lerp(_PLAY[idx][0], _PAUSE[idx][0], t)
                y = _lerp(_PLAY[idx][1], _PAUSE[idx][1], t)
                pt = QPointF(ox + x * s, oy + y * s)
                if j == 0:
                    path.moveTo(pt)
                else:
                    path.lineTo(pt)
            path.closeSubpath()
            painter.drawPath(path)

        painter.end()
