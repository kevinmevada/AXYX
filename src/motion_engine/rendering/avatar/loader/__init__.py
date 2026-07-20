"""Avatar asset loader package (Milestone 1)."""

from __future__ import annotations

from motion_engine.rendering.avatar.loader.avatar_loader import AvatarLoader
from motion_engine.rendering.avatar.loader.exceptions import (
    AssetNotFoundError,
    AvatarError,
    ManifestError,
    MaterialLoadError,
    MeshLoadError,
    SkeletonLoadError,
    TextureLoadError,
    ValidationError,
)
from motion_engine.rendering.avatar.loader.manifest_loader import ManifestLoader
from motion_engine.rendering.avatar.loader.material_loader import MaterialLoader
from motion_engine.rendering.avatar.loader.mesh_loader import MeshLoader
from motion_engine.rendering.avatar.loader.skeleton_loader import SkeletonLoader
from motion_engine.rendering.avatar.loader.texture_loader import TextureLoader

__all__ = [
    "AvatarLoader",
    "ManifestLoader",
    "MeshLoader",
    "TextureLoader",
    "MaterialLoader",
    "SkeletonLoader",
    "AvatarError",
    "ManifestError",
    "MeshLoadError",
    "TextureLoadError",
    "MaterialLoadError",
    "SkeletonLoadError",
    "ValidationError",
    "AssetNotFoundError",
]
