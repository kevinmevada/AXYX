"""StudioTheme dataclass and stylesheet entry points."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QWidget

from motion_engine.studio.theme.animations import StudioMotion
from motion_engine.studio.theme.colors import (
    DarkStudioColors,
    HighContrastStudioColors,
    StudioColors,
)
from motion_engine.studio.theme.fonts import register_studio_fonts
from motion_engine.studio.theme.icons import StudioIcons
from motion_engine.studio.theme.qss import assemble_stylesheet
from motion_engine.studio.theme.radius import StudioRadii
from motion_engine.studio.theme.shadows import apply_elevation as _apply_elevation
from motion_engine.studio.theme.spacing import StudioSpacing
from motion_engine.studio.theme.typography import StudioTypography


@dataclass(frozen=True, slots=True)
class StudioTheme:
    colors: StudioColors | DarkStudioColors | HighContrastStudioColors = StudioColors()
    spacing: StudioSpacing = StudioSpacing()
    radii: StudioRadii = StudioRadii()
    typography: StudioTypography = StudioTypography()
    icons: StudioIcons = StudioIcons()
    motion: StudioMotion = StudioMotion()
    name: str = "axyx_clinical_light"
    mode: str = "light"


# Clinical light is the product default.
DEFAULT_THEME = StudioTheme()
LIGHT_THEME = DEFAULT_THEME
DARK_THEME = StudioTheme(
    colors=DarkStudioColors(),
    name="axyx_flagship_dark",
    mode="dark",
)
HIGH_CONTRAST_THEME = StudioTheme(
    colors=HighContrastStudioColors(),
    name="axyx_high_contrast",
    mode="high_contrast",
)


def get_theme(mode: str = "light") -> StudioTheme:
    """Return a theme for ``mode`` (``light``, ``dark``, or ``high_contrast``)."""
    normalized = mode.lower()
    if normalized in {"dark", "night", "flagship"}:
        return DARK_THEME
    if normalized in {"high_contrast", "high-contrast", "a11y"}:
        return HIGH_CONTRAST_THEME
    return LIGHT_THEME


def apply_elevation(widget: QWidget, level: int = 1, *, color: str | None = None) -> None:
    """Apply soft elevation shadow to a widget."""
    _apply_elevation(
        widget,
        level,
        color=color,
        default_shadow=DEFAULT_THEME.colors.shadow,
    )


def build_stylesheet(theme: StudioTheme | None = None) -> str:
    """Application-wide stylesheet."""
    theme = theme or DEFAULT_THEME
    register_studio_fonts()
    return assemble_stylesheet(theme)
