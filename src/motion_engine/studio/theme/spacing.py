"""Spacing scale — 8-point grid."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StudioSpacing:
    """Allowed steps: 4 · 8 · 12 · 16 · 20 · 24 · 32 (+ 40 for rare chrome)."""

    xxs: int = 4
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 24
    xxl: int = 32
    xxxl: int = 40
