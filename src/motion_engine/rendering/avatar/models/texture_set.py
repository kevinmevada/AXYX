"""PBR texture slot set."""

from __future__ import annotations

from dataclasses import dataclass

from motion_engine.rendering.avatar.models.texture import TextureImage


@dataclass(frozen=True, slots=True)
class TextureSet:
    """Named PBR texture slots for one material."""

    albedo: TextureImage | None = None
    normal: TextureImage | None = None
    metallic: TextureImage | None = None
    roughness: TextureImage | None = None
    ao: TextureImage | None = None
    emissive: TextureImage | None = None
    packed_orm: TextureImage | None = None
    scatter: TextureImage | None = None


__all__ = ["TextureSet"]
