"""Motion Studio design system — tokens, QSS, elevation, and motion helpers.

Visual language: Apple Pro × Omniverse × soft clay elevation.
Layered surfaces, soft floating shadows, accent #4F8CFF.
Not heavy neumorphism — subtle lift only.

Elevation (``apply_elevation``)
-------------------------------
1 — Dock panels (sidebar, inspector) — soft float
2 — Cards / timeline / chrome chips
3 — Welcome / overlays

All colors / radii / spacing / fonts come from this package.
"""

from __future__ import annotations

from motion_engine.studio.theme.animations import (
    StudioMotion,
    fade_in,
    fade_out,
    slide,
)
from motion_engine.studio.theme.colors import DarkStudioColors, HighContrastStudioColors, StudioColors
from motion_engine.studio.theme.fonts import register_studio_fonts
from motion_engine.studio.theme.icons import StudioIcons, lucide_icon
from motion_engine.studio.theme.radius import StudioRadii
from motion_engine.studio.theme.spacing import StudioSpacing
from motion_engine.studio.theme.theme import (
    DARK_THEME,
    DEFAULT_THEME,
    HIGH_CONTRAST_THEME,
    StudioTheme,
    apply_elevation,
    build_stylesheet,
    get_theme,
)
from motion_engine.studio.theme.typography import StudioTypography

__all__ = [
    "DEFAULT_THEME",
    "DARK_THEME",
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
    "lucide_icon",
    "register_studio_fonts",
    "fade_in",
    "fade_out",
    "slide",
]
