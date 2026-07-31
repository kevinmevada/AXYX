"""Motion Studio design system — clinical light.

Calm tonal surfaces, Anodized Violet accent, soft elevation,
Inter Variable UI + Source Serif 4 wordmark.
"""
from __future__ import annotations

from motion_engine.studio.theme.animations import (
    StudioMotion,
    fade_in,
    fade_out,
    slide,
)
from motion_engine.studio.theme.colors import DarkStudioColors, HighContrastStudioColors, StudioColors
from motion_engine.studio.theme.fonts import (
    apply_app_font,
    register_studio_fonts,
    studio_display_font_family,
    studio_font_family,
)
from motion_engine.studio.theme.wordmark import (
    WORDMARK_INK,
    WORDMARK_WEIGHT_CHROME,
    WORDMARK_WEIGHT_HERO,
    WORDMARK_WEIGHT_UI,
    WORDMARK_Y,
    apply_chrome_wordmark_label,
    apply_wordmark_label,
    paint_wordmark,
    wordmark_html,
)
from motion_engine.studio.theme.icons import StudioIcons, lucide_icon
from motion_engine.studio.theme.palette import apply_museum_palette
from motion_engine.studio.theme.radius import StudioRadii
from motion_engine.studio.theme.spacing import StudioSpacing
from motion_engine.studio.theme.theme import (
    DARK_THEME,
    DEFAULT_THEME,
    HIGH_CONTRAST_THEME,
    LIGHT_THEME,
    StudioTheme,
    apply_elevation,
    build_stylesheet,
    get_theme,
)
from motion_engine.studio.theme.typography import StudioTypography

__all__ = [
    "DEFAULT_THEME",
    "DARK_THEME",
    "LIGHT_THEME",
    "HIGH_CONTRAST_THEME",
    "StudioTheme",
    "StudioColors",
    "DarkStudioColors",
    "HighContrastStudioColors",
    "get_theme",
    "StudioSpacing",
    "StudioRadii",
    "StudioTypography",
    "StudioIcons",
    "StudioMotion",
    "build_stylesheet",
    "apply_elevation",
    "apply_museum_palette",
    "lucide_icon",
    "register_studio_fonts",
    "apply_app_font",
    "studio_font_family",
    "studio_display_font_family",
    "WORDMARK_INK",
    "WORDMARK_Y",
    "WORDMARK_WEIGHT_HERO",
    "WORDMARK_WEIGHT_CHROME",
    "WORDMARK_WEIGHT_UI",
    "apply_wordmark_label",
    "apply_chrome_wordmark_label",
    "paint_wordmark",
    "wordmark_html",
    "fade_in",
    "fade_out",
    "slide",
]
