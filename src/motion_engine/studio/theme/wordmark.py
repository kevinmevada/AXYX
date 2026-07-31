"""AXYX brand wordmark — Source Serif 4 hero + Inter chrome + violet Y."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QLabel

from motion_engine.studio.theme.fonts import (
    studio_display_font_family,
    studio_font_family,
)

# Brand ink for A/X/X — Graphite Ink per brand treatment.
WORDMARK_INK = "#1C1E1C"
WORDMARK_Y = "#4B3F72"

# Hero: calm Semibold Source Serif (not display-Bold drama).
WORDMARK_WEIGHT_HERO = 600
# Chrome uses Inter at medium weight — not the display serif.
WORDMARK_WEIGHT_CHROME = 600
# Back-compat alias for loading / about serif marks.
WORDMARK_WEIGHT_UI = WORDMARK_WEIGHT_HERO


def wordmark_font(*, pixel_size: int, weight: int = WORDMARK_WEIGHT_HERO) -> QFont:
    """Source Serif 4 for hero wordmarks only — calm Semibold, not display Bold."""
    font = QFont(studio_display_font_family())
    font.setPixelSize(int(pixel_size))
    font.setWeight(QFont.Weight(int(weight)))
    font.setHintingPreference(QFont.HintingPreference.PreferDefaultHinting)
    font.setStyleStrategy(
        QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.PreferQuality
    )
    return font


def chrome_wordmark_font(*, pixel_size: int = 14) -> QFont:
    """Inter for top-bar / small chrome wordmarks."""
    font = QFont(studio_font_family())
    font.setPixelSize(int(pixel_size))
    font.setWeight(QFont.Weight(WORDMARK_WEIGHT_CHROME))
    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    return font


def wordmark_html(
    *,
    pixel_size: int | None = None,
    weight: int = WORDMARK_WEIGHT_HERO,
    family: str | None = None,
    ink: str = WORDMARK_INK,
    accent: str = WORDMARK_Y,
) -> str:
    """Rich-text AXYX with only the Y in accent violet."""
    fam = (family or studio_display_font_family()).replace("'", "\\'")
    size_css = f"font-size:{int(pixel_size)}px;" if pixel_size is not None else ""
    style = (
        f"font-family:'{fam}';font-weight:{int(weight)};{size_css}"
        "background:transparent;"
    )
    return (
        f'<span style="{style}">'
        f'<span style="color:{ink}">A</span>'
        f'<span style="color:{ink}">X</span>'
        f'<span style="color:{accent}">Y</span>'
        f'<span style="color:{ink}">X</span>'
        f"</span>"
    )


def apply_wordmark_label(
    label: QLabel,
    *,
    pixel_size: int,
    weight: int = WORDMARK_WEIGHT_HERO,
    object_name: str | None = None,
) -> None:
    """Configure a QLabel as the branded Source Serif 4 AXYX wordmark."""
    if object_name:
        label.setObjectName(object_name)
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setText(wordmark_html(pixel_size=pixel_size, weight=weight))
    label.setFont(wordmark_font(pixel_size=pixel_size, weight=weight))
    family = studio_display_font_family()
    sel = f"QLabel#{object_name}" if object_name else "QLabel"
    label.setStyleSheet(
        f"{sel} {{ font-family: '{family}'; font-size: {int(pixel_size)}px; "
        f"font-weight: {int(weight)}; background: transparent; }}"
    )


def apply_chrome_wordmark_label(
    label: QLabel,
    *,
    pixel_size: int = 14,
    object_name: str | None = "BrandTitle",
) -> None:
    """Small Inter wordmark for top-bar chrome — not the hero serif."""
    if object_name:
        label.setObjectName(object_name)
    family = studio_font_family()
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setText(
        wordmark_html(
            pixel_size=pixel_size,
            weight=WORDMARK_WEIGHT_CHROME,
            family=family,
        )
    )
    label.setFont(chrome_wordmark_font(pixel_size=pixel_size))
    sel = f"QLabel#{object_name}" if object_name else "QLabel"
    label.setStyleSheet(
        f"{sel} {{ font-family: '{family}'; font-size: {int(pixel_size)}px; "
        f"font-weight: {WORDMARK_WEIGHT_CHROME}; background: transparent; }}"
    )


def paint_wordmark(
    painter: QPainter,
    *,
    x: float,
    baseline: float,
    pixel_size: int,
    weight: int = WORDMARK_WEIGHT_HERO,
    letter_spacing: float = 0.0,
    ink: str = WORDMARK_INK,
    accent: str = WORDMARK_Y,
) -> float:
    """Draw AXYX with violet Y; returns advance width of the full mark."""
    font = wordmark_font(pixel_size=pixel_size, weight=weight)
    if letter_spacing:
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, letter_spacing)
    painter.setFont(font)
    metrics = QFontMetrics(font)
    cursor = float(x)
    for ch, color in (
        ("A", ink),
        ("X", ink),
        ("Y", accent),
        ("X", ink),
    ):
        painter.setPen(QColor(color))
        painter.drawText(int(round(cursor)), int(round(baseline)), ch)
        cursor += metrics.horizontalAdvance(ch)
    return cursor - x


def wordmark_advance(
    *,
    pixel_size: int,
    weight: int = WORDMARK_WEIGHT_HERO,
    letter_spacing: float = 0.0,
) -> tuple[int, int]:
    """Return (width, height) metrics for layout reservation."""
    font = wordmark_font(pixel_size=pixel_size, weight=weight)
    if letter_spacing:
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, letter_spacing)
    metrics = QFontMetrics(font)
    return metrics.horizontalAdvance("AXYX"), metrics.height()
