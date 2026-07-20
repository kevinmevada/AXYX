"""Loaded avatar runtime bundle (immutable)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from motion_engine.rendering.avatar.models.avatar_manifest import AvatarManifest
from motion_engine.rendering.avatar.models.material import MaterialData
from motion_engine.rendering.avatar.models.mesh import MeshData
from motion_engine.rendering.avatar.models.skeleton import AvatarSkeleton
from motion_engine.rendering.avatar.models.texture import TextureImage


@dataclass(frozen=True, slots=True)
class LoadedAvatar:
    """Immutable runtime avatar asset bundle in bind / rest pose.

    Produced by :class:`~motion_engine.rendering.avatar.loader.AvatarLoader`.

    Note:
        Distinct from the :class:`~motion_engine.rendering.avatar.avatar.Avatar`
        ABC used by ``AvatarManager``. Use ``DigitalAvatar`` to adapt.
    """

    id: str
    manifest: AvatarManifest
    meshes: tuple[MeshData, ...]
    materials: tuple[MaterialData, ...]
    skeleton: AvatarSkeleton | None
    textures: tuple[TextureImage, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def primary_mesh(self) -> MeshData | None:
        """First mesh, if any."""
        return self.meshes[0] if self.meshes else None


__all__ = ["LoadedAvatar"]
