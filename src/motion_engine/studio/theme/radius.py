"""Corner radius tokens for Motion Studio."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class StudioRadii:
    sm: int = 10
    md: int = 14  # buttons
    lg: int = 18  # cards
    xl: int = 20  # panels / viewport
    pill: int = 999
