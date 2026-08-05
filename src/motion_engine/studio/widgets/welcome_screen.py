"""Welcome — brand-first landing with glass panel + Source Serif boot.

Boot uses the same Source Serif 4 / violet-Y wordmark as the hero panel.
Entrance avoids QGraphicsBlurEffect (Windows lag/AV) and magnetic gimmicks —
a tight panel, restrained animation, compact primary CTA.

PERFORMANCE NOTE (this revision):
_GlassPanel used to rebuild its entire look (conic-gradient border stroke,
hairline, tiled noise) from scratch on every mouseMoveEvent. Stroking a
gradient pen along a rounded-rect path is one of the more expensive things
QPainter's raster backend does, and doing it 60x/sec while ALSO animating
the panel's position during entrance is what caused the visible lag.

Fix: the static card look is rendered once into a cached QPixmap (rebuilt
only on resize). Mouse movement now just blits that cached pixmap and
paints one small radial "sheen" circle on top, with the repaint throttled
to ~60fps and clipped to a small dirty rect instead of the whole widget.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PySide6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPoint,
    QPointF,
    QRectF,
    Qt,
    QTimer,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QConicalGradient,
    QDragEnterEvent,
    QDropEvent,
    QFont,
    QFontMetrics,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from motion_engine.studio.theme import DEFAULT_THEME
from motion_engine.studio.theme.fonts import studio_font_family
from motion_engine.studio.theme.wordmark import (
    WORDMARK_INK,
    WORDMARK_WEIGHT_HERO,
    WORDMARK_Y,
    paint_wordmark,
    wordmark_advance,
    wordmark_font,
)

_CTA_RADIUS = 8
_PANEL_RADIUS = 14
_BOOT_PIXEL = 72
_HERO_PIXEL = 72


def _safe_stop_anim(anim: QVariantAnimation | None) -> None:
    """Stop a QVariantAnimation even if DeleteWhenStopped already destroyed it."""
    if anim is None:
        return
    try:
        anim.stop()
    except RuntimeError:
        # C++ object already deleted (DeleteWhenStopped).
        pass


# Mouse-move driven repaints are coalesced to this interval instead of
# firing on every native move event (which can be 100s of Hz on some mice).
_SHEEN_THROTTLE_MS = 16  # ~60fps ceiling


def _is_dataset_path(path: Path) -> bool:
    return path.suffix.lower() in {".mat", ".npz", ".c3d", ".trc"}


def _build_noise_pixmap(size: int = 48, alpha: int = 8) -> QPixmap:
    """Small tileable grain — generated once, reused."""
    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    rng = random.Random(7)
    for y in range(size):
        for x in range(size):
            v = rng.randint(0, 255)
            image.setPixelColor(x, y, QColor(v, v, v, alpha))
    return QPixmap.fromImage(image)


class _BrandMark(QWidget):
    """Source Serif 4 AXYX — violet Y is the Y-axis of the capture volume."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("WelcomeBrandMark")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._pixel_size = _HERO_PIXEL
        self._reveal = 1.0
        self._update_size()

    def set_reveal(self, value: float) -> None:
        self._reveal = max(0.0, min(1.0, float(value)))
        self.update()

    def _update_size(self) -> None:
        width, height = wordmark_advance(
            pixel_size=self._pixel_size,
            weight=WORDMARK_WEIGHT_HERO,
            letter_spacing=0.0,
        )
        self.setFixedSize(max(width + 8, 240), max(height + 8, 78))

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        font = wordmark_font(pixel_size=self._pixel_size, weight=WORDMARK_WEIGHT_HERO)
        metrics = QFontMetrics(font)
        full_w = metrics.horizontalAdvance("AXYX")
        x0 = (self.width() - full_w) // 2
        baseline = (self.height() + metrics.ascent() - metrics.descent()) // 2 - 1
        paint_wordmark(
            painter,
            x=x0,
            baseline=baseline,
            pixel_size=self._pixel_size,
            weight=WORDMARK_WEIGHT_HERO,
            letter_spacing=0.0,
            ink=WORDMARK_INK,
            accent=WORDMARK_Y,
        )
        painter.end()


class _PaintedLine(QWidget):
    """Body text — QPainter, optional wrap so it never overflows the panel."""

    def __init__(
        self,
        text: str,
        *,
        pixel_size: int,
        weight: QFont.Weight,
        color: QColor,
        letter_spacing: float = 0.0,
        max_width: int = 320,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._text = text
        self._pixel_size = pixel_size
        self._weight = weight
        self._color = QColor(color)
        self._letter_spacing = letter_spacing
        self._max_width = max(120, int(max_width))
        self._alpha = 1.0
        self._update_size()

    def set_alpha(self, value: float) -> None:
        self._alpha = max(0.0, min(1.0, float(value)))
        self.update()

    def _font(self) -> QFont:
        font = QFont(studio_font_family())
        font.setPixelSize(self._pixel_size)
        font.setWeight(self._weight)
        if self._letter_spacing:
            font.setLetterSpacing(
                QFont.SpacingType.AbsoluteSpacing, self._letter_spacing
            )
        font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        return font

    def _update_size(self) -> None:
        metrics = QFontMetrics(self._font())
        # Bound width so wrapping measures against the glass content area.
        bound = QRectF(0, 0, float(self._max_width), 400.0)
        br = metrics.boundingRect(
            bound.toRect(),
            int(Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap),
            self._text,
        )
        self.setFixedSize(
            max(br.width() + 8, min(self._max_width, 220)),
            max(br.height() + 4, metrics.height() + 6),
        )

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        font = self._font()
        painter.setFont(font)
        color = QColor(self._color)
        color.setAlphaF(self._alpha * color.alphaF())
        painter.setPen(color)
        painter.drawText(
            self.rect(),
            int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
                | Qt.TextFlag.TextWordWrap),
            self._text,
        )
        painter.end()


class _CtaButton(QPushButton):
    """Compact primary CTA — solid accent, quiet color hover only."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("WelcomeCta")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._hover = False
        self._pressed = False
        c = DEFAULT_THEME.colors
        self._fill = QColor(c.accent)
        self._fill_hover = QColor(c.accent_hover)
        self._fill_pressed = QColor(c.accent_pressed)
        self._ink = QColor(c.text_on_accent)

    def enterEvent(self, event) -> None:  # noqa: N802
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hover = False
        self._pressed = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self._pressed = True
        self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        if self._pressed:
            fill = self._fill_pressed
        elif self._hover:
            fill = self._fill_hover
        else:
            fill = self._fill

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, float(_CTA_RADIUS), float(_CTA_RADIUS))

        if not self._pressed:
            edge = QLinearGradient(rect.topLeft(), rect.topRight())
            edge.setColorAt(0.0, QColor(255, 255, 255, 0))
            edge.setColorAt(0.5, QColor(255, 255, 255, 28 if self._hover else 18))
            edge.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setPen(QPen(edge, 1.0))
            painter.drawLine(
                QPointF(rect.left() + 10, rect.top() + 0.5),
                QPointF(rect.right() - 10, rect.top() + 0.5),
            )

        font = QFont(studio_font_family())
        font.setPixelSize(13)
        font.setWeight(QFont.Weight.Medium)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.4)
        painter.setFont(font)
        painter.setPen(self._ink)
        painter.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), self.text())
        painter.end()


class _BootOverlay(QWidget):
    """Scramble boot in Source Serif 4 — scramble only, fixed size (no enlarge)."""

    finished = Signal()

    _CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    _TARGET = "AXYX"
    _SCRAMBLE_MS = 2000
    _HOLD_MS = 480
    _FADE_MS = 720
    _SCRAMBLE_STEPS = 24

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self._progress = 0.0
        self._chars = list(self._TARGET)
        self._rng = random.Random(11)
        self._opacity = 1.0
        self._scramble_step = -1
        self._anim: QVariantAnimation | None = None
        self._fade_anim: QVariantAnimation | None = None

        self._font = wordmark_font(pixel_size=_BOOT_PIXEL, weight=WORDMARK_WEIGHT_HERO)
        self._metrics = QFontMetrics(self._font)
        self._slot_widths = [
            self._metrics.horizontalAdvance(ch) for ch in self._TARGET
        ]
        self._full_w = sum(self._slot_widths)
        self._ink = QColor(WORDMARK_INK)
        self._violet = QColor(WORDMARK_Y)
        self._bg = QColor(DEFAULT_THEME.colors.background)
        self._track = QColor(WORDMARK_Y)
        self._track.setAlpha(40)
        self._bar_fill = QColor(WORDMARK_Y)
        self._bar_fill.setAlpha(200)
        self._colors = (self._ink, self._ink, self._violet, self._ink)

    def start(self) -> None:
        _safe_stop_anim(self._anim)
        _safe_stop_anim(self._fade_anim)
        self._anim = None
        self._fade_anim = None
        self._progress = 0.0
        self._opacity = 1.0
        self._scramble_step = -1
        self._chars = list(self._TARGET)
        self._sync_chars(0.0)
        self.show()
        self.raise_()

        anim = QVariantAnimation(self)
        anim.setDuration(self._SCRAMBLE_MS)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        anim.valueChanged.connect(self._on_progress)
        anim.finished.connect(self._on_scramble_done)
        anim.start(QVariantAnimation.DeletionPolicy.DeleteWhenStopped)
        self._anim = anim

    def _on_progress(self, value: object) -> None:
        t = float(value)
        self._progress = t
        step = int(t * self._SCRAMBLE_STEPS)
        if step != self._scramble_step:
            self._scramble_step = step
            self._sync_chars(t)
        self._update_mark_region()

    def _sync_chars(self, t: float) -> None:
        n = len(self._TARGET)
        reveal_count = min(n, int(t * n + 1e-6) if t < 1.0 else n)
        if t >= 0.999:
            reveal_count = n
        chars: list[str] = []
        for i, ch in enumerate(self._TARGET):
            if i < reveal_count:
                chars.append(ch)
            else:
                chars.append(self._rng.choice(self._CHARSET))
        self._chars = chars

    def _on_scramble_done(self) -> None:
        self._progress = 1.0
        self._chars = list(self._TARGET)
        self._update_mark_region()
        QTimer.singleShot(self._HOLD_MS, self._fade_out)

    def _fade_out(self) -> None:
        _safe_stop_anim(self._fade_anim)
        self._fade_anim = None
        anim = QVariantAnimation(self)
        anim.setDuration(self._FADE_MS)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim.valueChanged.connect(self._set_opacity)

        def _done() -> None:
            self._fade_anim = None
            self._on_fade_done()

        anim.finished.connect(_done)
        anim.start(QVariantAnimation.DeletionPolicy.DeleteWhenStopped)
        self._fade_anim = anim

    def _set_opacity(self, value: object) -> None:
        self._opacity = float(value)
        self.update()

    def _on_fade_done(self) -> None:
        self.hide()
        self.finished.emit()

    def _mark_rect(self) -> QRectF:
        x0 = (self.width() - self._full_w) // 2
        baseline = self.height() // 2 + self._metrics.ascent() // 3
        top = baseline - self._metrics.ascent() - 8
        bar_y = baseline + self._metrics.descent() + 18
        bottom = bar_y + 8
        pad = 24
        return QRectF(
            x0 - pad,
            top,
            self._full_w + pad * 2,
            bottom - top,
        )

    def _update_mark_region(self) -> None:
        r = self._mark_rect().adjusted(-4, -4, 4, 4).toAlignedRect()
        self.update(r)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setOpacity(self._opacity)
        if event.rect() == self.rect() or self._opacity < 0.999:
            painter.fillRect(self.rect(), self._bg)
        else:
            painter.fillRect(event.rect(), self._bg)

        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setFont(self._font)
        x0 = (self.width() - self._full_w) // 2
        baseline = self.height() // 2 + self._metrics.ascent() // 3
        cursor = float(x0)
        for i, ch in enumerate(self._chars):
            slot_w = self._slot_widths[i]
            glyph_w = self._metrics.horizontalAdvance(ch)
            painter.setPen(self._colors[i])
            painter.drawText(
                int(round(cursor + (slot_w - glyph_w) * 0.5)),
                int(round(baseline)),
                ch,
            )
            cursor += slot_w

        bar_w = min(self._full_w, 200)
        bar_h = 2
        bar_x = (self.width() - bar_w) // 2
        bar_y = baseline + self._metrics.descent() + 18
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._track)
        painter.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 1, 1)
        painter.setBrush(self._bar_fill)
        painter.drawRoundedRect(
            bar_x, bar_y, int(bar_w * self._progress), bar_h, 1, 1
        )
        painter.end()


class _GlassPanel(QFrame):
    """Compact translucent card — grain + rim, cached base + throttled sheen.

    The static look (fill, conic-gradient rim stroke, hairline, noise tile)
    is expensive to compute per-frame, so it's rendered once into
    `self._base_pixmap` and only rebuilt on resize. Mouse movement redraws
    just a small radial sheen on top of the cached image, throttled to
    ~60fps via a coalescing QTimer instead of repainting on every native
    move event.
    """

    _noise_pixmap: QPixmap | None = None

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("WelcomeGlassPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMouseTracking(True)
        self._mouse_pos: QPointF | None = None
        self._pending_mouse_pos: QPointF | None = None
        self._sheen_opacity = 0.0
        self._sheen_anim: QVariantAnimation | None = None
        self._base_pixmap: QPixmap | None = None
        self._base_pixmap_size = (-1, -1)

        if _GlassPanel._noise_pixmap is None:
            _GlassPanel._noise_pixmap = _build_noise_pixmap()

        # Coalesces rapid mouse-move events into one repaint per tick,
        # so we never do more work than ~60 paints/sec regardless of how
        # fast the OS delivers move events.
        self._move_timer = QTimer(self)
        self._move_timer.setInterval(_SHEEN_THROTTLE_MS)
        self._move_timer.setSingleShot(False)
        self._move_timer.timeout.connect(self._apply_pending_mouse_pos)

    # -- cached base rendering ------------------------------------------------

    def resizeEvent(self, event) -> None:  # noqa: N802
        self._base_pixmap = None
        super().resizeEvent(event)

    def _ensure_base_pixmap(self) -> QPixmap:
        size = (self.width(), self.height())
        if self._base_pixmap is not None and self._base_pixmap_size == size:
            return self._base_pixmap

        dpr = self.devicePixelRatioF()
        pm = QPixmap(int(self.width() * dpr), int(self.height() * dpr))
        pm.setDevicePixelRatio(dpr)
        pm.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pm)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(rect, _PANEL_RADIUS, _PANEL_RADIUS)

        accent = QColor(WORDMARK_Y)

        painter.setClipPath(path)
        painter.fillRect(self.rect(), QColor(255, 255, 255, 150))

        # Static rim gradient (angle fixed at 90° when idle — the "premium"
        # rotating rim only happens on hover via the animated sheen below,
        # kept cheap by living in the cached pixmap otherwise).
        center = rect.center()
        conic = QConicalGradient(center, 90.0)
        bright = QColor(255, 255, 255, 160)
        dim = QColor(accent.red(), accent.green(), accent.blue(), 28)
        conic.setColorAt(0.0, bright)
        conic.setColorAt(0.18, dim)
        conic.setColorAt(0.5, dim)
        conic.setColorAt(0.82, dim)
        conic.setColorAt(1.0, bright)
        painter.setPen(QPen(conic, 1.1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        painter.setPen(QPen(QColor(28, 30, 28, 18), 1.0))
        painter.drawPath(path)

        hairline = QLinearGradient(rect.topLeft(), rect.topRight())
        hairline.setColorAt(0.0, QColor(255, 255, 255, 0))
        hairline.setColorAt(0.5, QColor(255, 255, 255, 180))
        hairline.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setPen(QPen(hairline, 1.0))
        painter.drawLine(
            QPointF(rect.left() + 24, rect.top() + 1),
            QPointF(rect.right() - 24, rect.top() + 1),
        )

        if _GlassPanel._noise_pixmap is not None:
            painter.setOpacity(0.35)
            painter.drawTiledPixmap(self.rect(), _GlassPanel._noise_pixmap)
            painter.setOpacity(1.0)

        painter.end()

        self._base_pixmap = pm
        self._base_pixmap_size = size
        return pm

    # -- mouse-driven sheen (cheap, partial-repaint only) ---------------------

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        # Just record where the cursor is; the timer applies it at a fixed
        # cadence so a fast mouse can't force more repaints than the
        # throttle interval allows.
        self._pending_mouse_pos = event.position()
        if not self._move_timer.isActive():
            self._move_timer.start()
        super().mouseMoveEvent(event)

    def _apply_pending_mouse_pos(self) -> None:
        if self._pending_mouse_pos is None:
            self._move_timer.stop()
            return
        old_pos = self._mouse_pos
        self._mouse_pos = self._pending_mouse_pos
        self._pending_mouse_pos = None
        self._repaint_sheen_region(old_pos)
        self._repaint_sheen_region(self._mouse_pos)

    def _repaint_sheen_region(self, pos: QPointF | None) -> None:
        if pos is None:
            return
        radius = 160
        r = QRectF(
            pos.x() - radius, pos.y() - radius, radius * 2, radius * 2
        ).toAlignedRect()
        self.update(r)

    def enterEvent(self, event) -> None:  # noqa: N802
        self._animate_sheen(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        old_pos = self._mouse_pos
        self._mouse_pos = None
        self._pending_mouse_pos = None
        self._move_timer.stop()
        self._animate_sheen(0.0)
        self._repaint_sheen_region(old_pos)
        super().leaveEvent(event)

    def _animate_sheen(self, target: float) -> None:
        _safe_stop_anim(self._sheen_anim)
        self._sheen_anim = None
        anim = QVariantAnimation(self)
        anim.setDuration(180)
        anim.setStartValue(self._sheen_opacity)
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.valueChanged.connect(self._set_sheen_opacity)

        def _clear() -> None:
            if self._sheen_anim is anim:
                self._sheen_anim = None

        anim.finished.connect(_clear)
        anim.start(QVariantAnimation.DeletionPolicy.DeleteWhenStopped)
        self._sheen_anim = anim

    def _set_sheen_opacity(self, value: object) -> None:
        self._sheen_opacity = float(value)
        self._repaint_sheen_region(self._mouse_pos)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Blit the cached glass card — this is the whole fix: no gradient
        # stroking or noise tiling happens per-frame anymore.
        painter.drawPixmap(0, 0, self._ensure_base_pixmap())

        if self._sheen_opacity > 0.001 and self._mouse_pos is not None:
            rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
            path = QPainterPath()
            path.addRoundedRect(rect, _PANEL_RADIUS, _PANEL_RADIUS)
            painter.setClipPath(path)

            sheen = QRadialGradient(self._mouse_pos, 160)
            sheen.setColorAt(0.0, QColor(255, 255, 255, int(55 * self._sheen_opacity)))
            sheen.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
            painter.fillPath(path, sheen)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        painter.end()


class WelcomeScreen(QWidget):
    """Upper-stage welcome — boot → tight glass panel → one CTA."""

    openDatasetRequested = Signal()
    datasetDropped = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("WelcomeRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self._entered = False
        self._anim_group: QParallelAnimationGroup | None = None
        self._panel_opacity = 0.0

        c = DEFAULT_THEME.colors

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(1)

        self._panel = _GlassPanel(self)
        self._panel.setFixedWidth(400)
        self._panel.setMouseTracking(True)

        # Cheap opacity fade for the entrance (no blur — GPU-light, and
        # QGraphicsOpacityEffect doesn't have the Windows softwarerender
        # cost that QGraphicsBlurEffect does).
        self._panel_opacity_effect = QGraphicsOpacityEffect(self._panel)
        self._panel_opacity_effect.setOpacity(0.0)
        self._panel.setGraphicsEffect(self._panel_opacity_effect)

        panel_layout = QVBoxLayout(self._panel)
        panel_layout.setContentsMargins(28, 24, 28, 22)
        panel_layout.setSpacing(0)

        self._brand = _BrandMark()
        panel_layout.addWidget(self._brand, alignment=Qt.AlignmentFlag.AlignCenter)

        panel_layout.addSpacing(10)
        self._support = _PaintedLine(
            "Open a gait dataset to explore subjects and reconstruct motion.",
            pixel_size=13,
            weight=QFont.Weight.Normal,
            color=QColor(c.text_secondary),
            max_width=340,
        )
        panel_layout.addWidget(self._support, alignment=Qt.AlignmentFlag.AlignCenter)

        panel_layout.addSpacing(18)
        self._cta = QStackedWidget()
        self._cta.setFixedWidth(200)
        self._cta.setFixedHeight(40)

        self._open_btn = _CtaButton("Open Dataset")
        self._open_btn.setFixedHeight(40)
        self._open_btn.setFixedWidth(200)
        self._open_btn.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self._open_btn.clicked.connect(self.openDatasetRequested.emit)

        opening = QFrame()
        opening.setObjectName("WelcomeOpening")
        opening.setFixedHeight(40)
        opening_layout = QVBoxLayout(opening)
        opening_layout.setContentsMargins(8, 4, 8, 4)
        opening_layout.setSpacing(6)
        opening_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._opening_label = QLabel("Opening…")
        self._opening_label.setObjectName("WelcomeOpeningLabel")
        self._opening_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._opening_label.setStyleSheet(
            f"color: {c.accent}; font-size: 12px; font-weight: 600; background: transparent;"
        )
        self._opening_bar = QProgressBar()
        self._opening_bar.setObjectName("WelcomeOpeningBar")
        self._opening_bar.setRange(0, 100)
        self._opening_bar.setValue(0)
        self._opening_bar.setTextVisible(False)
        self._opening_bar.setFixedHeight(3)
        self._opening_bar.setMinimumWidth(160)
        opening_layout.addWidget(self._opening_label)
        opening_layout.addWidget(self._opening_bar)

        self._cta.addWidget(self._open_btn)
        self._cta.addWidget(opening)
        self._cta.setCurrentIndex(0)
        panel_layout.addWidget(self._cta, alignment=Qt.AlignmentFlag.AlignCenter)

        outer.addWidget(self._panel, alignment=Qt.AlignmentFlag.AlignCenter)
        outer.addStretch(1)

        self._boot = _BootOverlay(self)
        self._boot.setGeometry(self.rect())
        self._boot.finished.connect(self._play_panel_entrance)

        self._brand.set_reveal(1.0)
        self._support.set_alpha(0.0)
        self._cta.setEnabled(False)
        self._cta.hide()
        self._panel.setVisible(False)

    def resizeEvent(self, event) -> None:  # noqa: N802
        self._boot.setGeometry(self.rect())
        super().resizeEvent(event)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        if not self._entered:
            self._entered = True
            self._panel.setVisible(False)
            QTimer.singleShot(40, self._boot.start)

    def _play_panel_entrance(self) -> None:
        """Soft slide + fade — no overshoot scale."""
        self._panel.setVisible(True)
        self._panel.raise_()

        group = QParallelAnimationGroup(self)

        end_pos = self._panel.pos()
        travel = 16
        self._panel.move(end_pos + QPoint(0, travel))
        self._panel_opacity_effect.setOpacity(0.0)

        slide_anim = QVariantAnimation(self)
        slide_anim.setDuration(560)
        slide_anim.setStartValue(0.0)
        slide_anim.setEndValue(1.0)
        slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _apply_slide(v: object, end=end_pos, t=travel) -> None:
            progress = float(v)
            self._panel.move(end + QPoint(0, int(round(t * (1.0 - progress)))))
            self._panel_opacity_effect.setOpacity(max(0.0, min(1.0, progress)))

        slide_anim.valueChanged.connect(_apply_slide)
        group.addAnimation(slide_anim)

        support_anim = QVariantAnimation(self)
        support_anim.setDuration(480)
        support_anim.setStartValue(0.0)
        support_anim.setEndValue(1.0)
        support_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        support_anim.valueChanged.connect(self._support.set_alpha)
        group.addAnimation(support_anim)

        def _show_cta() -> None:
            self._cta.show()
            self._cta.setEnabled(True)

        QTimer.singleShot(320, _show_cta)

        self._anim_group = group
        group.start()

    def set_opening(self, opening: bool, progress: int | None = None) -> None:
        if opening:
            self._cta.setCurrentIndex(1)
            self._open_btn.setEnabled(False)
            if progress is not None:
                self._opening_bar.setValue(max(0, min(100, int(progress))))
        else:
            self._cta.setCurrentIndex(0)
            self._open_btn.setEnabled(True)
            self._opening_bar.setValue(0)
            self._opening_label.setText("Opening…")

    def set_opening_progress(self, value: int) -> None:
        if self._cta.currentIndex() != 1:
            return
        self._opening_bar.setValue(min(98, max(0, int(value))))

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile() and _is_dataset_path(Path(url.toLocalFile())):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            path = Path(url.toLocalFile())
            if _is_dataset_path(path):
                event.acceptProposedAction()
                self.datasetDropped.emit(str(path))
                return
        event.ignore()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(DEFAULT_THEME.colors.background))
        painter.end()