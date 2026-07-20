"""Soft contact-shadow parameters for the light studio floor."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContactShadowParams:
    """Soft gray foot / body contact shadows (not black void discs)."""

    rgb: tuple[float, float, float] = (0.42, 0.43, 0.46)
    foot_opacity: float = 0.22
    body_opacity: float = 0.08


__all__ = ["ContactShadowParams"]
