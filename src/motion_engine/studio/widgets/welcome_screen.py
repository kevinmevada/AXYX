"""Welcome — brand-first landing with Source Serif 4 hero + Inter chrome."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPoint,
    Qt,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QFont,
    QFontMetrics,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QFrame,
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

_CTA_RADIUS = 10


def _is_dataset_path(path: Path) -> bool:
    return path.suffix.lower() in {".mat", ".npz", ".c3d", ".trc"}


class _BrandMark(QWidget):
    """Source Serif 4 AXYX — violet Y is the Y-axis of the capture volume."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("WelcomeBrandMark")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._pixel_size = 96
        self._reveal = 0.0
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
        self.setFixedSize(max(width + 24, 320), max(height + 20, 110))

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        font = wordmark_font(pixel_size=self._pixel_size, weight=WORDMARK_WEIGHT_HERO)
        metrics = QFontMetrics(font)
        violet = QColor(WORDMARK_Y)

        full_w = metrics.horizontalAdvance("AXYX")
        x0 = (self.width() - full_w) // 2
        baseline = (self.height() + metrics.ascent() - metrics.descent()) // 2 - 2
        reveal_x = x0 + int(full_w * self._reveal) + 2

        painter.save()
        painter.setClipRect(0, 0, reveal_x, self.height())
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
        painter.restore()

        if 0.02 < self._reveal < 0.995:
            edge = QPen(violet)
            edge.setWidthF(1.25)
            painter.setPen(edge)
            top = baseline - metrics.ascent() + 6
            bottom = baseline + metrics.descent() + 2
            painter.drawLine(QPoint(reveal_x, top), QPoint(reveal_x, bottom))

        painter.end()


class _PaintedLine(QWidget):
    """Single-line text painted with QPainter — immune to QSS font crush."""

    def __init__(
        self,
        text: str,
        *,
        pixel_size: int,
        weight: QFont.Weight,
        color: QColor,
        letter_spacing: float = 0.0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._text = text
        self._pixel_size = pixel_size
        self._weight = weight
        self._color = QColor(color)
        self._letter_spacing = letter_spacing
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
        self.setFixedSize(
            max(metrics.horizontalAdvance(self._text) + 24, 280),
            metrics.height() + 12,
        )

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        font = self._font()
        painter.setFont(font)
        metrics = QFontMetrics(font)
        color = QColor(self._color)
        color.setAlphaF(self._alpha * color.alphaF())
        painter.setPen(color)
        x = (self.width() - metrics.horizontalAdvance(self._text)) // 2
        baseline = (self.height() + metrics.ascent() - metrics.descent()) // 2
        painter.drawText(x, baseline, self._text)
        painter.end()


class _CtaButton(QPushButton):
    """Primary CTA — 10px radius rectangle (not a capsule)."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("PrimaryButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
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
        rect = self.rect().adjusted(1, 1, -1, -1)
        if self._pressed:
            fill = self._fill_pressed
        elif self._hover:
            fill = self._fill_hover
        else:
            fill = self._fill
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, float(_CTA_RADIUS), float(_CTA_RADIUS))
        font = QFont(studio_font_family())
        font.setPixelSize(14)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.setPen(self._ink)
        painter.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), self.text())
        painter.end()


class WelcomeScreen(QWidget):
    """Upper-stage welcome — one hero, one job, one CTA."""

    openDatasetRequested = Signal()
    datasetDropped = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("WelcomeRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAcceptDrops(True)
        self._entered = False
        self._anim_group: QParallelAnimationGroup | None = None

        c = DEFAULT_THEME.colors

        root = QVBoxLayout(self)
        root.setContentsMargins(72, 56, 72, 24)
        root.setSpacing(0)
        # Anchor in the upper stage under the persistent command bar.
        root.addSpacing(28)

        self._brand = _BrandMark()
        root.addWidget(self._brand, alignment=Qt.AlignmentFlag.AlignCenter)

        root.addSpacing(20)
        # One job: explain the CTA. Brand voice lives in the wordmark alone.
        self._support = _PaintedLine(
            "Open a gait dataset to explore subjects and reconstruct motion.",
            pixel_size=15,
            weight=QFont.Weight.Normal,
            color=QColor(c.text_secondary),
        )
        root.addWidget(self._support, alignment=Qt.AlignmentFlag.AlignCenter)

        root.addSpacing(36)
        self._cta = QStackedWidget()
        self._cta.setFixedWidth(280)
        self._cta.setMinimumHeight(52)

        self._open_btn = _CtaButton("Open Dataset")
        self._open_btn.setMinimumHeight(52)
        self._open_btn.setMinimumWidth(260)
        self._open_btn.setFixedHeight(52)
        self._open_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._open_btn.clicked.connect(self.openDatasetRequested.emit)

        opening = QFrame()
        opening.setObjectName("WelcomeOpening")
        opening.setMinimumHeight(52)
        opening_layout = QVBoxLayout(opening)
        opening_layout.setContentsMargins(16, 10, 16, 10)
        opening_layout.setSpacing(8)
        opening_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._opening_label = QLabel("Opening…")
        self._opening_label.setObjectName("WelcomeOpeningLabel")
        self._opening_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._opening_label.setStyleSheet(
            f"color: {c.accent}; font-size: 14px; font-weight: 600; background: transparent;"
        )
        self._opening_bar = QProgressBar()
        self._opening_bar.setObjectName("WelcomeOpeningBar")
        self._opening_bar.setRange(0, 100)
        self._opening_bar.setValue(0)
        self._opening_bar.setTextVisible(False)
        self._opening_bar.setFixedHeight(4)
        self._opening_bar.setMinimumWidth(220)
        opening_layout.addWidget(self._opening_label)
        opening_layout.addWidget(self._opening_bar)

        self._cta.addWidget(self._open_btn)
        self._cta.addWidget(opening)
        self._cta.setCurrentIndex(0)
        root.addWidget(self._cta, alignment=Qt.AlignmentFlag.AlignCenter)

        root.addSpacing(14)
        self._hint = _PaintedLine(
            "Drop a dataset here  ·  Ctrl+O",
            pixel_size=12,
            weight=QFont.Weight.Medium,
            color=QColor(c.text_muted),
            letter_spacing=0.3,
        )
        root.addWidget(self._hint, alignment=Qt.AlignmentFlag.AlignCenter)

        root.addStretch(1)

        self._brand.set_reveal(0.0)
        for w in (self._support, self._hint):
            w.set_alpha(0.0)
        self._cta.setEnabled(False)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        if not self._entered:
            self._entered = True
            self._play_entrance()

    def _play_entrance(self) -> None:
        if self._anim_group is not None:
            self._anim_group.stop()

        group = QParallelAnimationGroup(self)

        trace = QVariantAnimation(self)
        trace.setDuration(720)
        trace.setStartValue(0.0)
        trace.setEndValue(1.0)
        trace.setEasingCurve(QEasingCurve.Type.OutCubic)
        trace.valueChanged.connect(self._brand.set_reveal)
        group.addAnimation(trace)

        def _fade(target, delay: int, duration: int = 400) -> None:
            anim = QVariantAnimation(self)
            anim.setDuration(delay + duration)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)

            def apply(v, widget=target, d=delay, dur=duration) -> None:
                total = d + dur
                local = 0.0 if total <= 0 else max(0.0, (float(v) * total - d) / dur)
                widget.set_alpha(min(1.0, local))

            anim.valueChanged.connect(apply)
            group.addAnimation(anim)

        _fade(self._support, 380)
        _fade(self._hint, 620)

        self._cta.hide()
        show_cta = QVariantAnimation(self)
        show_cta.setDuration(520)
        show_cta.setStartValue(0)
        show_cta.setEndValue(1)

        def _show_cta() -> None:
            self._cta.show()
            self._cta.setEnabled(True)

        show_cta.finished.connect(_show_cta)
        group.addAnimation(show_cta)

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
