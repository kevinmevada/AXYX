"""Floor reflection parameter helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FloorReflectionParams:
    """Slightly reflective pale floor — photography studio, not a mirror."""

    metallic: float = 0.08
    roughness: float = 0.72
    specular: float = 0.08


__all__ = ["FloorReflectionParams"]
