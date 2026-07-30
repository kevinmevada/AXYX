"""Typography tokens for Motion Studio."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StudioTypography:
    family: str = (
        "'Inter', 'SF Pro Text', 'Segoe UI Variable', 'Segoe UI', sans-serif"
    )
    family_mono: str = (
        "'SF Mono', 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace"
    )
    size_xs: int = 12   # values
    size_sm: int = 13   # labels
    size_md: int = 14
    size_lg: int = 15   # section headers
    size_xl: int = 18   # panel titles
    size_xxl: int = 22
    size_display: int = 28
    tracking_tight: str = "-0.3px"
    tracking_wide: str = "0.3px"
    tracking_caps: str = "0.8px"
