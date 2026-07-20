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
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

from motion_engine.studio.theme import DEFAULT_THEME

ICON_XS = DEFAULT_THEME.icons.xs
ICON_SM = DEFAULT_THEME.icons.sm
ICON_MD = DEFAULT_THEME.icons.md
ICON_LG = DEFAULT_THEME.icons.lg


def _ink(active: bool = False) -> QColor:
    c = DEFAULT_THEME.colors
    return QColor(c.accent if active else c.text_secondary)


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


def icon_play(size: int = ICON_MD, *, active: bool = False) -> QIcon:
    """Return a play triangle icon."""
    pix = _base_pixmap(size)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(_ink(active))
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


def icon_stop(size: int = ICON_MD, *, active: bool = False) -> QIcon:
    """Return a stop icon."""
    pix = _base_pixmap(size)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(_ink(active))
    painter.setPen(Qt.PenStyle.NoPen)
    side = size * 0.42
    painter.drawRoundedRect(
        QRectF((size - side) / 2, (size - side) / 2, side, side), 3, 3
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


def icon_app(size: int = 64) -> QIcon:
    """Premium app mark - soft white card + accent gait path."""
    pix = _base_pixmap(size)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(DEFAULT_THEME.colors.surface_raised))
    painter.setPen(QPen(QColor(DEFAULT_THEME.colors.border), 1.0))
    painter.drawRoundedRect(QRectF(2, 2, size - 4, size - 4), size * 0.22, size * 0.22)
    painter.setPen(QPen(QColor(DEFAULT_THEME.colors.accent), max(2.0, size * 0.055)))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(size * 0.22, size * 0.68)
    path.cubicTo(
        QPointF(size * 0.36, size * 0.28),
        QPointF(size * 0.58, size * 0.78),
        QPointF(size * 0.78, size * 0.34),
    )
    painter.drawPath(path)
    painter.setBrush(QColor(DEFAULT_THEME.colors.accent))
    painter.setPen(Qt.PenStyle.NoPen)
    for cx, cy in (
        (size * 0.22, size * 0.68),
        (size * 0.48, size * 0.50),
        (size * 0.78, size * 0.34),
    ):
        painter.drawEllipse(QPointF(cx, cy), size * 0.05, size * 0.05)
    painter.end()
    return QIcon(pix)


def splash_pixmap(width: int = 560, height: int = 320) -> QPixmap:
    """Create a splash screen pixmap."""
    pix = QPixmap(width, height)
    pix.fill(QColor(DEFAULT_THEME.colors.background))
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(DEFAULT_THEME.colors.surface))
    painter.setPen(QPen(QColor(DEFAULT_THEME.colors.border_subtle), 1))
    r = DEFAULT_THEME.radii.xl
    painter.drawRoundedRect(
        QRectF(
            DEFAULT_THEME.spacing.xl,
            DEFAULT_THEME.spacing.xl,
            width - DEFAULT_THEME.spacing.xxl,
            height - DEFAULT_THEME.spacing.xxl,
        ),
        r,
        r,
    )
    mark = icon_app(72).pixmap(72, 72)
    painter.drawPixmap(int(width * 0.5 - 36), 70, mark)
    painter.setPen(QColor(DEFAULT_THEME.colors.text_primary))
    font = painter.font()
    font.setPointSize(DEFAULT_THEME.typography.size_xl)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(
        QRectF(0, 160, width, 40),
        int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
        "AXYX",
    )
    font.setPointSize(DEFAULT_THEME.typography.size_sm)
    font.setBold(False)
    painter.setFont(font)
    painter.setPen(QColor(DEFAULT_THEME.colors.text_secondary))
    painter.drawText(
        QRectF(0, 200, width, 30),
        int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
        "Commercial biomechanics workspace",
    )
    painter.end()
    return pix
