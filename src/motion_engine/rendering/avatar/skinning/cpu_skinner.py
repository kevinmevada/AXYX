"""CPU linear-blend skinning (vectorized NumPy)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from motion_engine.rendering.avatar.models.mesh import MeshData
from motion_engine.rendering.avatar.skinning.matrix_palette import MatrixPalette
from motion_engine.rendering.avatar.skinning.types import Float32Array
from motion_engine.rendering.avatar.skinning.vertex_transform import (
    blend_directions,
    blend_points,
)
from motion_engine.rendering.avatar.skinning.weight_table import WeightTable


@dataclass(frozen=True, slots=True)
class SkinningResult:
    """Deformed attribute buffers (independently owned)."""

    positions: Float32Array
    normals: Float32Array
    tangents: Float32Array | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "positions", np.asarray(self.positions, dtype=np.float32).copy())
        object.__setattr__(self, "normals", np.asarray(self.normals, dtype=np.float32).copy())
        if self.tangents is not None:
            object.__setattr__(
                self, "tangents", np.asarray(self.tangents, dtype=np.float32).copy()
            )


class CpuSkinner:
    """Deterministic CPU LBS skinner (thread-safe: no shared mutable state)."""

    def skin(
        self,
        mesh: MeshData,
        weights: WeightTable,
        palette: MatrixPalette,
        *,
        deform_normals: bool = True,
        tangents: np.ndarray | None = None,
    ) -> SkinningResult:
        """Deform mesh attributes. Never mutates ``mesh``."""
        mats = palette.as_array()
        # Remap: weight indices are skeleton bone indices for identity palette.
        pos = blend_points(mesh.positions, mats, weights.joint_indices, weights.joint_weights)
        if deform_normals and mesh.normals.size:
            nrm = blend_directions(
                mesh.normals, mats, weights.joint_indices, weights.joint_weights
            )
        else:
            nrm = np.asarray(mesh.normals, dtype=np.float32).copy()
        tan_out = None
        if tangents is not None:
            tan_out = blend_directions(
                tangents, mats, weights.joint_indices, weights.joint_weights
            )
        return SkinningResult(positions=pos, normals=nrm, tangents=tan_out)


__all__ = ["CpuSkinner", "SkinningResult"]
