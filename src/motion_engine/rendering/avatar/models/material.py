"""Immutable material model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from motion_engine.rendering.avatar.models.texture_set import TextureSet


@dataclass(frozen=True, slots=True)
class MaterialData:
    """Immutable PBR material description (Milestone 1).

    Designed for future expansion (clearcoat, transmission, etc.) via
    :attr:`extras` without breaking callers.
    """

    name: str
    base_color: tuple[float, float, float] = (0.8, 0.8, 0.8)
    metallic: float = 0.0
    roughness: float = 0.5
    emissive: tuple[float, float, float] = (0.0, 0.0, 0.0)
    textures: TextureSet = field(default_factory=TextureSet)
    extras: Mapping[str, Any] = field(default_factory=dict)


__all__ = ["MaterialData"]
