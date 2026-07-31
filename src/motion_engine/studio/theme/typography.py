"""Typography tokens — Inter UI + Source Serif 4 display."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StudioTypography:
    """Inter for chrome; Source Serif 4 for brand wordmark moments."""

    family: str = (
        "'Inter Variable', 'Inter', 'SF Pro Text', 'Segoe UI Variable', "
        "'Segoe UI', sans-serif"
    )
    family_display: str = (
        "'Source Serif 4', 'Georgia', 'Times New Roman', serif"
    )
    family_mono: str = (
        "'IBM Plex Mono', 'JetBrains Mono', 'Cascadia Code', 'SF Mono', "
        "'Consolas', monospace"
    )
    # Metadata / section caps
    size_xs: int = 11
    # Secondary / chrome
    size_sm: int = 12
    # Primary body / list rows
    size_md: int = 14
    # Emphasized secondary
    size_lg: int = 13
    # Application title
    size_xl: int = 21
    size_xxl: int = 22
    size_display: int = 22
    tracking_tight: str = "-0.2px"
    tracking_wide: str = "0.4px"
    tracking_caps: str = "0.96px"  # ~+8% at 12px
