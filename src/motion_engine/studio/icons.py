"""Programmatic icon factory for AXYX.
Icon system
-----------
* Size grid: 16 / 20 / 24 / 32 (``StudioIcons`` / ``ICON_*`` constants).
* Stroke weight: ``DEFAULT_THEME.icons.stroke`` (1.6px) for outline icons.
* Color: ``text_secondary`` at rest, ``accent`` when active / checked.
* Prefer filled geometric glyphs for transport (play/pause) so hit targets
  read clearly at 20-24px; keep stroke icons for chrome actions.
"""
from __future__ import annotations
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFontMetrics, QIcon, QPainter, QPainterPath, QPen, QPixmap
from motion_engine.studio.theme import DEFAULT_THEME
from motion_engine.studio.theme.wordmark import (
    WORDMARK_WEIGHT_UI,
    paint_wordmark,
    wordmark_font,
)
from motion_engine.studio.theme.fonts import register_studio_fonts, studio_font_family
ICON_XS = DEFAULT_THEME.icons.xs
ICON_SM = DEFAULT_THEME.icons.sm
ICON_MD = DEFAULT_THEME.icons.md
ICON_LG = DEFAULT_THEME.icons.lg

def _ink(active: bool = False) -> QColor:
    c = DEFAULT_THEME.colors
    return QColor(c.accent if active else c.text_secondary)


def _on_accent() -> QColor:
    return QColor(DEFAULT_THEME.colors.text_on_accent)


def _base_pixmap(size: int = ICON_MD) -> QPixmap:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    return pix


def _stroke_pen(active: bool = False, size: int = ICON_MD) -> QPen:
    pen = QPen(_ink(active))
    pen.setWidthF(DEFAULT_THEME.icons.stroke)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def icon_play(size: int = ICON_MD, *, active: bool = False, on_gold: bool = False) -> QIcon:
    """Return a play triangle icon."""
    pix = _base_pixmap(size)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(_on_accent() if on_gold else _ink(active))
    painter.setPen(Qt.PenStyle.NoPen)
    path = QPainterPath()
    path.moveTo(size * 0.32, size * 0.22)
    path.lineTo(size * 0.78, size * 0.50)
    path.lineTo(size * 0.32, size * 0.78)
    path.closeSubpath()
    painter.drawPath(path)
    painter.end()
    return QIcon(pix)

def icon_pause(size: int = ICON_MD, *, active: bool = False) -> QIcon:
    """Return a pause icon."""
    pix = _base_pixmap(size)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(_ink(active))
    painter.setPen(Qt.PenStyle.NoPen)
    w = size * 0.16
    h = size * 0.52
    y = size * 0.24
    painter.drawRoundedRect(QRectF(size * 0.30, y, w, h), 2, 2)
    painter.drawRoundedRect(QRectF(size * 0.54, y, w, h), 2, 2)
    painter.end()
    return QIcon(pix)

def icon_stop(size: int = ICON_MD, *, active: bool = False, danger: bool = False) -> QIcon:
    """Return a stop icon — danger red filled square (Museum White exception)."""
    pix = _base_pixmap(size)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    if danger:
        color = QColor(DEFAULT_THEME.colors.danger)
    else:
        color = _ink(active)
    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    # Slightly larger than flanking chevrons so the red reads at a glance.
    side = size * (0.48 if danger else 0.42)
    painter.drawRoundedRect(
        QRectF((size - side) / 2, (size - side) / 2, side, side), 2, 2
    )
    painter.end()
    return QIcon(pix)

def icon_prev(size: int = ICON_MD, *, active: bool = False) -> QIcon:
    """Return previous-frame icon."""
    pix = _base_pixmap(size)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    color = _ink(active)
    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(QRectF(size * 0.24, size * 0.28, size * 0.12, size * 0.44), 2, 2)
    path = QPainterPath()
    path.moveTo(size * 0.72, size * 0.24)
    path.lineTo(size * 0.40, size * 0.50)
    path.lineTo(size * 0.72, size * 0.76)
    path.closeSubpath()
    painter.drawPath(path)
    painter.end()
    return QIcon(pix)

def icon_next(size: int = ICON_MD, *, active: bool = False) -> QIcon:
    """Return next-frame icon."""
    pix = _base_pixmap(size)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    color = _ink(active)
    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    path = QPainterPath()
    path.moveTo(size * 0.28, size * 0.24)
    path.lineTo(size * 0.60, size * 0.50)
    path.lineTo(size * 0.28, size * 0.76)
    path.closeSubpath()
    painter.drawPath(path)
    painter.drawRoundedRect(QRectF(size * 0.64, size * 0.28, size * 0.12, size * 0.44), 2, 2)
    painter.end()
    return QIcon(pix)

def icon_display(size: int = ICON_SM, *, active: bool = False) -> QIcon:
    """Stroke icon for the Display menu button."""
    pix = _base_pixmap(size)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(_stroke_pen(active, size))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    margin = size * 0.22
    painter.drawRoundedRect(
        QRectF(margin, margin, size - 2 * margin, size - 2 * margin),
        3,
        3,
    )
    painter.drawLine(
        QPointF(size * 0.28, size * 0.55),
        QPointF(size * 0.72, size * 0.55),
    )
    painter.end()
    return QIcon(pix)


def icon_chevron_down(size: int = ICON_SM, *, active: bool = False) -> QIcon:
    """Down chevron for expanded sections / menu buttons."""
    pix = _base_pixmap(size)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = _stroke_pen(active, size)
    pen.setWidthF(max(1.4, DEFAULT_THEME.icons.stroke))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(size * 0.28, size * 0.38)
    path.lineTo(size * 0.50, size * 0.62)
    path.lineTo(size * 0.72, size * 0.38)
    painter.drawPath(path)
    painter.end()
    return QIcon(pix)


def icon_chevron_right(size: int = ICON_SM, *, active: bool = False) -> QIcon:
    """Right chevron for collapsed sections."""
    pix = _base_pixmap(size)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = _stroke_pen(active, size)
    pen.setWidthF(max(1.4, DEFAULT_THEME.icons.stroke))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(size * 0.38, size * 0.28)
    path.lineTo(size * 0.62, size * 0.50)
    path.lineTo(size * 0.38, size * 0.72)
    painter.drawPath(path)
    painter.end()
    return QIcon(pix)

def icon_app(size: int = 64) -> QIcon:
    """AXYX mark — pure black kinematic-chain glyph on a white card.

    Three joints + two bones, drawn as a deliberate stride silhouette
    (hip -> knee -> ankle). No gradients, no accent color, no dot-path
    filler shapes — a single confident ink stroke, black and white only.
    """
    pix = _base_pixmap(size)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#FFFFFF"))
    painter.setPen(QPen(QColor("#111111"), max(1.2, size * 0.03)))
    painter.drawRoundedRect(QRectF(2, 2, size - 4, size - 4), size * 0.2, size * 0.2)

    bone_pen = QPen(QColor("#111111"), max(2.4, size * 0.08))
    bone_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(bone_pen)
    hip = QPointF(size * 0.30, size * 0.28)
    knee = QPointF(size * 0.66, size * 0.46)
    ankle = QPointF(size * 0.36, size * 0.76)
    painter.drawLine(hip, knee)
    painter.drawLine(knee, ankle)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#111111"))
    for joint, radius in ((hip, size * 0.075), (knee, size * 0.09), (ankle, size * 0.075)):
        painter.drawEllipse(joint, radius, radius)
    painter.end()
    return QIcon(pix)

def splash_pixmap(width: int = 560, height: int = 340) -> QPixmap:
    """Branded black & white splash pixmap.

    Layout is split into two fixed, non-overlapping bands so nothing can
    collide: a white card with the mark + wordmark on top, and a solid
    black footer strip reserved exclusively for the loading status text
    drawn later by ``QSplashScreen.showMessage``. Previously the status
    text was painted in white directly over the (near-white) background,
    which is why it could show up as a faint stray artifact at startup.
    """
    pix = QPixmap(width, height)
    pix.fill(QColor("#111111"))
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    footer_h = 44
    card_h = height - footer_h
    painter.setBrush(QColor("#FFFFFF"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRect(QRectF(0, 0, width, card_h))

    mark = icon_app(76).pixmap(76, 76)
    painter.drawPixmap(int(width * 0.5 - 38), int(card_h * 0.28 - 38), mark)

    register_studio_fonts()
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    mark_size = 28
    wm_font = wordmark_font(pixel_size=mark_size, weight=WORDMARK_WEIGHT_UI)
    wm_font.setLetterSpacing(wm_font.SpacingType.AbsoluteSpacing, 1.0)
    metrics = QFontMetrics(wm_font)
    advance = metrics.horizontalAdvance("AXYX")
    band_top = card_h * 0.28 + 46
    baseline = band_top + (40 + metrics.ascent() - metrics.descent()) / 2.0
    paint_wordmark(
        painter,
        x=(width - advance) / 2.0,
        baseline=baseline,
        pixel_size=mark_size,
        weight=WORDMARK_WEIGHT_UI,
        letter_spacing=1.0,
    )
    font = painter.font()
    font.setFamily(studio_font_family())
    font.setPointSize(DEFAULT_THEME.typography.size_sm)
    font.setBold(False)
    font.setLetterSpacing(font.SpacingType.AbsoluteSpacing, 0.6)
    painter.setFont(font)
    painter.setPen(QColor("#5A5A5A"))
    painter.drawText(
        QRectF(0, card_h * 0.28 + 84, width, 26),
        int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
        "Commercial biomechanics workspace",
    )

    painter.setPen(QPen(QColor("#2A2A2A"), 1))
    painter.drawLine(QPointF(0, card_h), QPointF(width, card_h))
    painter.end()
    return pix
