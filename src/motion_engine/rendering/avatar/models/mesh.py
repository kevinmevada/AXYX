"""Immutable mesh models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.floating]
IntArray = NDArray[np.integer]


@dataclass(frozen=True, slots=True)
class SubMesh:
    """Index range into the parent mesh index buffer."""

    name: str
    index_offset: int
    index_count: int
    material_name: str = "default"


@dataclass(frozen=True, slots=True)
class MeshBounds:
    """Axis-aligned bounds and bounding sphere."""

    aabb_min: tuple[float, float, float]
    aabb_max: tuple[float, float, float]
    center: tuple[float, float, float]
    radius: float


@dataclass(frozen=True, slots=True)
class MeshData:
    """Immutable triangle mesh in bind / rest pose.

    Skinning attributes are optional and unused until Milestone 3.
    """

    name: str
    positions: FloatArray
    normals: FloatArray
    uvs: FloatArray
    indices: IntArray
    vertex_colors: FloatArray | None = None
    submeshes: tuple[SubMesh, ...] = ()
    bounds: MeshBounds | None = None
    joint_indices: IntArray | None = None
    joint_weights: FloatArray | None = None
    source_path: Path | None = None
    format: str = "unknown"

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "positions", np.asarray(self.positions, dtype=np.float32).copy()
        )
        object.__setattr__(
            self, "normals", np.asarray(self.normals, dtype=np.float32).copy()
        )
        object.__setattr__(self, "uvs", np.asarray(self.uvs, dtype=np.float32).copy())
        object.__setattr__(
            self, "indices", np.asarray(self.indices, dtype=np.int32).copy()
        )
        if self.vertex_colors is not None:
            object.__setattr__(
                self,
                "vertex_colors",
                np.asarray(self.vertex_colors, dtype=np.float32).copy(),
            )
        if self.joint_indices is not None:
            object.__setattr__(
                self,
                "joint_indices",
                np.asarray(self.joint_indices, dtype=np.int32).copy(),
            )
        if self.joint_weights is not None:
            object.__setattr__(
                self,
                "joint_weights",
                np.asarray(self.joint_weights, dtype=np.float32).copy(),
            )

    @property
    def vertex_count(self) -> int:
        return int(self.positions.shape[0])

    @property
    def triangle_count(self) -> int:
        return int(self.indices.size // 3)


def compute_bounds(positions: np.ndarray) -> MeshBounds:
    """Compute AABB + sphere from ``(N, 3)`` positions."""
    pts = np.asarray(positions, dtype=np.float64)
    if pts.size == 0:
        return MeshBounds((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 0.0)
    mn = pts.min(axis=0)
    mx = pts.max(axis=0)
    center = 0.5 * (mn + mx)
    radius = float(np.linalg.norm(pts - center, axis=1).max())
    return MeshBounds(
        aabb_min=(float(mn[0]), float(mn[1]), float(mn[2])),
        aabb_max=(float(mx[0]), float(mx[1]), float(mx[2])),
        center=(float(center[0]), float(center[1]), float(center[2])),
        radius=radius,
    )


__all__ = ["SubMesh", "MeshBounds", "MeshData", "compute_bounds"]
