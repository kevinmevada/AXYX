"""Color tokens for Motion Studio."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StudioColors:
    """Layered light surfaces + dark viewport + Apple-style accents."""

    background: str = "#ECECEC"
    surface: str = "#F5F5F7"
    surface_raised: str = "#FFFFFF"
    surface_sunken: str = "#E8E8ED"
    surface_overlay: str = "#F0F0F3"
    glass: str = "rgba(255, 255, 255, 0.55)"
    glass_strong: str = "rgba(255, 255, 255, 0.72)"
    glass_subtle: str = "rgba(255, 255, 255, 0.38)"
    glass_border: str = "rgba(255, 255, 255, 0.9)"
    glass_edge: str = "rgba(209, 209, 214, 0.55)"
    control: str = "rgba(255, 255, 255, 0.6)"

    border: str = "#E5E5EA"
    border_subtle: str = "#ECECEF"
    border_strong: str = "#D1D1D6"
    highlight: str = "#FFFFFF"
    shadow_soft: str = "#000000"

    text_primary: str = "#1D1D1F"
    text_secondary: str = "#1D1D1F"
    text_muted: str = "#1D1D1F"
    text_disabled: str = "#8E8E93"
    text_on_accent: str = "#FFFFFF"

    accent: str = "#4F8CFF"
    accent_hover: str = "#6BA0FF"
    accent_pressed: str = "#3A74E0"
    accent_glow: str = "#4F8CFF"
    cyan: str = "#5AC8F5"
    selection_fill: str = "#E8F0FF"
    accent_muted: str = "#E8F0FF"
    accent_border: str = "#B8D0FF"

    success: str = "#34C759"
    success_muted: str = "#E4F8EA"
    warning: str = "#FF9F0A"
    warning_muted: str = "#FFF3E0"
    danger: str = "#FF453A"
    danger_muted: str = "#FFE5E3"

    focus_ring: str = "#4F8CFF"
    shadow: str = "#000000"
    overlay_scrim: str = "#1D1D1F"
    viewport_void: str = "#EEEEEF"
    gradient_top: str = "#F4F4F6"
    gradient_mid: str = "#EAEAEE"
    gradient_bottom: str = "#E2E2E7"


@dataclass(frozen=True, slots=True)
class DarkStudioColors:
    """Dark surfaces for night / lab viewing."""

    background: str = "#1C1C1E"
    surface: str = "#2C2C2E"
    surface_raised: str = "#3A3A3C"
    surface_sunken: str = "#141416"
    surface_overlay: str = "#252528"
    glass: str = "rgba(44, 44, 46, 0.72)"
    glass_strong: str = "rgba(58, 58, 60, 0.88)"
    glass_subtle: str = "rgba(28, 28, 30, 0.55)"
    glass_border: str = "rgba(72, 72, 74, 0.9)"
    glass_edge: str = "rgba(72, 72, 74, 0.55)"
    control: str = "rgba(58, 58, 60, 0.75)"

    border: str = "#38383A"
    border_subtle: str = "#2C2C2E"
    border_strong: str = "#48484A"
    highlight: str = "#48484A"
    shadow_soft: str = "#000000"

    text_primary: str = "#F5F5F7"
    text_secondary: str = "#EBEBF0"
    text_muted: str = "#AEAEB2"
    text_disabled: str = "#636366"
    text_on_accent: str = "#FFFFFF"

    accent: str = "#5E9CFF"
    accent_hover: str = "#7AADFF"
    accent_pressed: str = "#4786E8"
    accent_glow: str = "#5E9CFF"
    cyan: str = "#64D2FF"
    selection_fill: str = "#1E3A5F"
    accent_muted: str = "#1E3A5F"
    accent_border: str = "#3A5F99"

    success: str = "#30D158"
    success_muted: str = "#1E3D28"
    warning: str = "#FFD60A"
    warning_muted: str = "#3D3518"
    danger: str = "#FF453A"
    danger_muted: str = "#3D1E1C"

    focus_ring: str = "#5E9CFF"
    shadow: str = "#000000"
    overlay_scrim: str = "#000000"
    viewport_void: str = "#121214"
    gradient_top: str = "#1C1C1E"
    gradient_mid: str = "#252528"
    gradient_bottom: str = "#141416"


@dataclass(frozen=True, slots=True)
class HighContrastStudioColors:
    """High-contrast black / white / yellow for accessibility."""

    background: str = "#000000"
    surface: str = "#0A0A0A"
    surface_raised: str = "#111111"
    surface_sunken: str = "#000000"
    surface_overlay: str = "#1A1A1A"
    glass: str = "rgba(0, 0, 0, 0.92)"
    glass_strong: str = "rgba(10, 10, 10, 0.98)"
    glass_subtle: str = "rgba(0, 0, 0, 0.75)"
    glass_border: str = "#FFFFFF"
    glass_edge: str = "#FFFFFF"
    control: str = "#111111"

    border: str = "#FFFFFF"
    border_subtle: str = "#CCCCCC"
    border_strong: str = "#FFFFFF"
    highlight: str = "#FFFFFF"
    shadow_soft: str = "#000000"

    text_primary: str = "#FFFFFF"
    text_secondary: str = "#FFFFFF"
    text_muted: str = "#E0E0E0"
    text_disabled: str = "#888888"
    text_on_accent: str = "#000000"

    accent: str = "#FFD600"
    accent_hover: str = "#FFEA00"
    accent_pressed: str = "#E6C200"
    accent_glow: str = "#FFD600"
    cyan: str = "#00FFFF"
    selection_fill: str = "#333300"
    accent_muted: str = "#333300"
    accent_border: str = "#FFD600"

    success: str = "#00FF00"
    success_muted: str = "#003300"
    warning: str = "#FFD600"
    warning_muted: str = "#333300"
    danger: str = "#FF4444"
    danger_muted: str = "#330000"

    focus_ring: str = "#FFD600"
    shadow: str = "#000000"
    overlay_scrim: str = "#000000"
    viewport_void: str = "#000000"
    gradient_top: str = "#000000"
    gradient_mid: str = "#0A0A0A"
    gradient_bottom: str = "#111111"
