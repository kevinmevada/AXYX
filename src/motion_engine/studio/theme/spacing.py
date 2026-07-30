"""Spacing scale tokens for Motion Studio."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StudioSpacing:
    xxs: int = 2
    xs: int = 4
    sm: int = 8
    md: int = 16
    lg: int = 24
    xl: int = 32
    xxl: int = 40
    xxxl: int = 56
