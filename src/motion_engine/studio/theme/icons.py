"""Lucide SVG icon loader for Motion Studio."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_REPO_ROOT = Path(__file__).resolve().parents[4]
_STUDIO_ASSETS = Path(__file__).resolve().parents[1] / "assets"

_LUCIDE_ALIASES: dict[str, str] = {
    "play": "play",
    "pause": "pause",
    "stop": "square",
    "square": "square",
    "chevron-left": "chevron-left",
    "chevron-right": "chevron-right",
    "chevron-up": "chevron-up",
    "chevron-down": "chevron-down",
    "monitor": "monitor",
    "display": "monitor",
    "settings": "settings",
    "search": "search",
    "folder": "folder",
    "folder-open": "folder-open",
    "x": "x",
    "close": "x",
    "menu": "menu",
    "plus": "plus",
    "minus": "minus",
    "refresh": "refresh-cw",
    "loop": "repeat",
    "repeat": "repeat",
    "skip-back": "skip-back",
    "skip-forward": "skip-forward",
    "prev": "chevron-left",
    "next": "chevron-right",
}


@dataclass(frozen=True, slots=True)
class StudioIcons:
    xs: int = 16
    sm: int = 18
    md: int = 20
    lg: int = 28
    stroke: float = 1.5


def _lucide_search_roots() -> tuple[Path, ...]:
    return (
        _REPO_ROOT / "assets" / "icons" / "lucide",
        _STUDIO_ASSETS / "icons" / "lucide",
    )


def _resolve_lucide_path(name: str) -> Path | None:
    file_name = f"{_LUCIDE_ALIASES.get(name, name)}.svg"
    for root in _lucide_search_roots():
        candidate = root / file_name
        if candidate.is_file():
            return candidate
    return None


def _tint_svg(svg_text: str, color: str) -> str:
    """Replace stroke/fill colors in Lucide SVG markup."""
    tinted = re.sub(
        r'stroke="[^"]*"',
        f'stroke="{color}"',
        svg_text,
    )
    tinted = re.sub(
        r'fill="(?!none)[^"]*"',
        f'fill="{color}"',
        tinted,
    )
    return tinted


def _fallback_icon(size: int, color: str, name: str) -> QIcon:
    """Simple monogram fallback when the SVG asset is missing."""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor(color))
    font = painter.font()
    font.setPixelSize(max(8, size // 2))
    font.setBold(True)
    painter.setFont(font)
    letter = (name[:1] or "?").upper()
    painter.drawText(pix.rect(), int(Qt.AlignmentFlag.AlignCenter), letter)
    painter.end()
    return QIcon(pix)


def lucide_icon(name: str, size: int = 20, color: str = "#1D1D1F") -> QIcon:
    """Load a Lucide SVG from ``assets/icons/lucide`` and return a ``QIcon``."""
    return _lucide_icon_cached(name, size, color)


@lru_cache(maxsize=256)
def _lucide_icon_cached(name: str, size: int, color: str) -> QIcon:
    path = _resolve_lucide_path(name)
    if path is None:
        return _fallback_icon(size, color, name)

    svg_text = path.read_text(encoding="utf-8")
    tinted = _tint_svg(svg_text, color)
    renderer = QSvgRenderer(tinted.encode("utf-8"))
    if not renderer.isValid():
        return _fallback_icon(size, color, name)

    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()
    return QIcon(pix)
