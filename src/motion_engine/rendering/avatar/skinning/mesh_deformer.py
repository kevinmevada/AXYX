"""Deformed mesh output — preserves source topology / UVs."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from motion_engine.rendering.avatar.models.mesh import MeshBounds, MeshData, compute_bounds
from motion_engine.rendering.avatar.skinning.cpu_skinner import SkinningResult
from motion_engine.rendering.avatar.skinning.types import Float32Array, Int32Array


@dataclass(frozen=True, slots=True)
class DeformedMesh:
    """Immutable snapshot of a deformed mesh (source mesh never modified)."""

    name: str
    positions: Float32Array
    normals: Float32Array
    uvs: Float32Array
    indices: Int32Array
    bounds: MeshBounds
    source_mesh_name: str = ""
    tangents: Float32Array | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "positions", np.asarray(self.positions, dtype=np.float32).copy())
        object.__setattr__(self, "normals", np.asarray(self.normals, dtype=np.float32).copy())
        object.__setattr__(self, "uvs", np.asarray(self.uvs, dtype=np.float32).copy())
        object.__setattr__(self, "indices", np.asarray(self.indices, dtype=np.int32).copy())
        if self.tangents is not None:
            object.__setattr__(
                self, "tangents", np.asarray(self.tangents, dtype=np.float32).copy()
            )

    @property
    def vertex_count(self) -> int:
        return int(self.positions.shape[0])

    @property
    def triangle_count(self) -> int:
        return int(self.indices.size // 3)


class MeshDeformer:
    """Build :class:`DeformedMesh` from source mesh + skinning result."""

    def deform(self, source: MeshData, result: SkinningResult, *, name: str | None = None) -> DeformedMesh:
        """Create deformed mesh; UVs/indices copied from source (topology preserved)."""
        bounds = compute_bounds(result.positions)
        return DeformedMesh(
            name=name or f"deformed:{source.name}",
            positions=result.positions,
            normals=result.normals,
            uvs=np.asarray(source.uvs, dtype=np.float32).copy(),
            indices=np.asarray(source.indices, dtype=np.int32).copy(),
            bounds=bounds,
            source_mesh_name=source.name,
            tangents=result.tangents,
        )


__all__ = ["DeformedMesh", "MeshDeformer"]
