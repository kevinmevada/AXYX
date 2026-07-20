"""Immutable avatar asset models (Milestone 1)."""

from __future__ import annotations

from motion_engine.rendering.avatar.models.avatar import LoadedAvatar
from motion_engine.rendering.avatar.models.avatar_manifest import (
    AvatarManifest,
    CoordinateSystem,
    LodEntry,
)
from motion_engine.rendering.avatar.models.material import MaterialData
from motion_engine.rendering.avatar.models.mesh import (
    MeshBounds,
    MeshData,
    SubMesh,
    compute_bounds,
)
from motion_engine.rendering.avatar.models.skeleton import AvatarSkeleton, BoneData
from motion_engine.rendering.avatar.models.texture import TextureImage
from motion_engine.rendering.avatar.models.texture_set import TextureSet

__all__ = [
    "CoordinateSystem",
    "LodEntry",
    "AvatarManifest",
    "TextureImage",
    "TextureSet",
    "MaterialData",
    "SubMesh",
    "MeshBounds",
    "MeshData",
    "compute_bounds",
    "BoneData",
    "AvatarSkeleton",
    "LoadedAvatar",
]
