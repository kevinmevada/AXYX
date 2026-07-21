"""CPU-side caches for mesh / palette / skinning results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Hashable

from motion_engine.rendering.avatar.models.mesh import MeshData
from motion_engine.rendering.avatar.skinning.matrix_palette import MatrixPalette
from motion_engine.rendering.avatar.skinning.mesh_deformer import DeformedMesh
from motion_engine.rendering.avatar.skinning.mesh_skin import MeshSkin


@dataclass
class SkinningCache:
    """Simple key→value caches (no rendering dependencies)."""

    meshes: dict[Hashable, MeshData] = field(default_factory=dict)
    skins: dict[Hashable, MeshSkin] = field(default_factory=dict)
    palettes: dict[Hashable, MatrixPalette] = field(default_factory=dict)
    deformed: dict[Hashable, DeformedMesh] = field(default_factory=dict)
    hits: int = 0
    misses: int = 0

    def get_deformed(self, key: Hashable) -> DeformedMesh | None:
        v = self.deformed.get(key)
        if v is None:
            self.misses += 1
            return None
        self.hits += 1
        return v

    def put_deformed(self, key: Hashable, mesh: DeformedMesh) -> None:
        self.deformed[key] = mesh

    def clear(self) -> None:
        self.meshes.clear()
        self.skins.clear()
        self.palettes.clear()
        self.deformed.clear()
        self.hits = 0
        self.misses = 0


# Alias name from spec
MeshCache = SkinningCache

__all__ = ["SkinningCache", "MeshCache"]
