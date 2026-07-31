"""Corner radius tokens — soft clinical radii."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StudioRadii:
    sm: int = 4
    md: int = 8
    lg: int = 12
    xl: int = 16
    cta: int = 10  # Primary CTA — radius'd rectangle, not a capsule
    pill: int = 999
