"""Color tokens for Motion Studio — calm clinical light default."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StudioColors:
    """Museum White — Anodized Violet accent + Graphite Ink typography."""

    background: str = "#FCFCFD"
    surface: str = "#FFFFFF"
    surface_raised: str = "#FFFFFF"
    surface_sunken: str = "#F8F9FB"
    surface_overlay: str = "#EDEAF2"
    glass: str = "#FCFCFD"
    glass_strong: str = "#FFFFFF"
    glass_subtle: str = "#F8F9FB"
    glass_border: str = "#E7EAF0"
    glass_edge: str = "#E7EAF0"
    control: str = "transparent"

    border: str = "#E7EAF0"
    border_subtle: str = "#E7EAF0"
    border_strong: str = "#D8DCE6"
    highlight: str = "#F3F5F9"
    shadow_soft: str = "rgba(28, 30, 28, 0.10)"

    # Primary text is true black; secondary stays readable charcoal (not dull grey).
    text_primary: str = "#000000"
    text_secondary: str = "#2A2A2A"
    text_muted: str = "#3D3D3D"
    text_disabled: str = "#6E6E6B"
    text_on_accent: str = "#FFFFFF"

    # Anodized Violet — UI chrome metal (viewport joints use separate glow colors)
    accent: str = "#4B3F72"
    accent_hover: str = "#5C5085"
    accent_pressed: str = "#3A3159"
    accent_glow: str = "rgba(75, 63, 114, 0.28)"
    cyan: str = "#3D3D3D"
    selection_fill: str = "#EDEAF2"
    accent_muted: str = "#EDEAF2"
    accent_border: str = "#4B3F72"

    success: str = "#3D6B4A"
    success_muted: str = "#E7EDE9"
    warning: str = "#8A6A2A"
    warning_muted: str = "#EFEBE2"
    danger: str = "#B5473B"
    danger_muted: str = "#F8EBE9"

    focus_ring: str = "#4B3F72"
    shadow: str = "rgba(0, 0, 0, 0.12)"
    overlay_scrim: str = "rgba(255, 255, 255, 0.82)"
    viewport_void: str = "#FFFFFF"
    gradient_top: str = "#FCFCFD"
    gradient_mid: str = "#FCFCFD"
    gradient_bottom: str = "#F8F9FB"
    glow_gold: str = "transparent"
    glow_violet: str = "rgba(75, 63, 114, 0.18)"
    glow_blue: str = "transparent"
    divider: str = "#E7EAF0"
    panel_top_sheen: str = "transparent"
    hover: str = "#F3F5F9"


@dataclass(frozen=True, slots=True)
class DarkStudioColors:
    """Legacy Flagship dark — kept for ``theme_mode=dark``."""

    background: str = "#0B090D"
    surface: str = "#111010"
    surface_raised: str = "#161412"
    surface_sunken: str = "#0A080A"
    surface_overlay: str = "#1A1714"
    glass: str = "rgba(17, 16, 16, 0.78)"
    glass_strong: str = "rgba(17, 16, 16, 0.88)"
    glass_subtle: str = "rgba(17, 16, 16, 0.72)"
    glass_border: str = "rgba(255, 255, 255, 0.08)"
    glass_edge: str = "rgba(255, 255, 255, 0.08)"
    control: str = "rgba(255, 255, 255, 0.10)"

    border: str = "rgba(255, 255, 255, 0.12)"
    border_subtle: str = "rgba(255, 255, 255, 0.08)"
    border_strong: str = "rgba(255, 255, 255, 0.18)"
    highlight: str = "rgba(255, 255, 255, 0.06)"
    shadow_soft: str = "#000000"

    text_primary: str = "#F1EEE8"
    text_secondary: str = "#A29D94"
    text_muted: str = "#78766E"
    text_disabled: str = "#5C5A54"
    text_on_accent: str = "#0B090D"

    accent: str = "#D0AC68"
    accent_hover: str = "#DEC28C"
    accent_pressed: str = "#78623A"
    accent_glow: str = "#C4A05C"
    cyan: str = "#A29D94"
    selection_fill: str = "rgba(208, 172, 104, 0.30)"
    accent_muted: str = "rgba(208, 172, 104, 0.18)"
    accent_border: str = "#D0AC68"

    success: str = "#7FAE8C"
    success_muted: str = "rgba(127, 174, 140, 0.18)"
    warning: str = "#DEC28C"
    warning_muted: str = "rgba(222, 194, 140, 0.18)"
    danger: str = "#D25A5A"
    danger_muted: str = "rgba(210, 90, 90, 0.20)"

    focus_ring: str = "#D0AC68"
    shadow: str = "#000000"
    overlay_scrim: str = "#000000"
    viewport_void: str = "#0A0809"
    gradient_top: str = "#0B090D"
    gradient_mid: str = "#13100F"
    gradient_bottom: str = "#0E0B10"
    glow_gold: str = "rgba(196, 160, 92, 0.28)"
    glow_violet: str = "rgba(120, 70, 130, 0.14)"
    glow_blue: str = "rgba(60, 90, 140, 0.12)"
    divider: str = "rgba(255, 255, 255, 0.16)"
    panel_top_sheen: str = "rgba(255, 255, 255, 0.04)"
    hover: str = "rgba(255, 255, 255, 0.06)"


@dataclass(frozen=True, slots=True)
class HighContrastStudioColors:
    """High-contrast — Graphite Ink + Anodized Violet accent."""

    background: str = "#FFFFFF"
    surface: str = "#FFFFFF"
    surface_raised: str = "#FFFFFF"
    surface_sunken: str = "#F0F0F0"
    surface_overlay: str = "#EDEAF2"
    glass: str = "#FFFFFF"
    glass_strong: str = "#FFFFFF"
    glass_subtle: str = "#FFFFFF"
    glass_border: str = "#1C1E1C"
    glass_edge: str = "#1C1E1C"
    control: str = "#FFFFFF"

    border: str = "#1C1E1C"
    border_subtle: str = "#6E6E6B"
    border_strong: str = "#1C1E1C"
    highlight: str = "#F3F5F9"
    shadow_soft: str = "transparent"

    text_primary: str = "#000000"
    text_secondary: str = "#2A2A2A"
    text_muted: str = "#3D3D3D"
    text_disabled: str = "#6E6E6B"
    text_on_accent: str = "#FFFFFF"

    accent: str = "#4B3F72"
    accent_hover: str = "#5C5085"
    accent_pressed: str = "#3A3159"
    accent_glow: str = "#4B3F72"
    cyan: str = "#3D3D3D"
    selection_fill: str = "#EDEAF2"
    accent_muted: str = "#EDEAF2"
    accent_border: str = "#4B3F72"

    success: str = "#006600"
    success_muted: str = "#CCFFCC"
    warning: str = "#996600"
    warning_muted: str = "#FFF0CC"
    danger: str = "#B5473B"
    danger_muted: str = "#FFCCCC"

    focus_ring: str = "#4B3F72"
    shadow: str = "transparent"
    overlay_scrim: str = "#FFFFFF"
    viewport_void: str = "#FFFFFF"
    gradient_top: str = "#FFFFFF"
    gradient_mid: str = "#FFFFFF"
    gradient_bottom: str = "#FFFFFF"
    glow_gold: str = "transparent"
    glow_violet: str = "transparent"
    glow_blue: str = "transparent"
    divider: str = "#1C1E1C"
    panel_top_sheen: str = "transparent"
    hover: str = "#F3F5F9"
