"""Avatar asset-pipeline exceptions (Milestone 1).

Extends the frozen rendering error hierarchy with loader-specific types.
"""

from __future__ import annotations

from motion_engine.rendering.errors import (
    AvatarLoadError,
    MaterialLoadError,
    MeshLoadError,
    RenderErrorCode,
    ResourceNotFoundError,
    TextureLoadError,
)


class AvatarError(AvatarLoadError):
    """Base error for avatar asset pipeline failures."""

    code = RenderErrorCode.AVATAR_LOAD


class ManifestError(AvatarError):
    """Invalid, unsupported, or unreadable ``avatar.json``."""


class SkeletonLoadError(AvatarError):
    """Skeleton hierarchy / bind data failed to load."""


class ValidationError(AvatarError):
    """Asset or manifest validation failed."""


class AssetNotFoundError(AvatarError, ResourceNotFoundError):
    """Referenced asset path does not exist."""

    code = RenderErrorCode.RESOURCE_NOT_FOUND


__all__ = [
    "AvatarError",
    "ManifestError",
    "MeshLoadError",
    "TextureLoadError",
    "MaterialLoadError",
    "SkeletonLoadError",
    "ValidationError",
    "AssetNotFoundError",
    "AvatarLoadError",
    "ResourceNotFoundError",
]
