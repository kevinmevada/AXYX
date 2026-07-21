"""Dense weight tables for mesh skinning."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from motion_engine.rendering.avatar.skinning.constants import (
    DEFAULT_MAX_INFLUENCES,
    UNUSED_BONE_INDEX,
)
from motion_engine.rendering.avatar.skinning.types import Float32Array, Int32Array
from motion_engine.rendering.avatar.skinning.vertex_influence import influence_counts


@dataclass(frozen=True, slots=True)
class WeightTable:
    """Per-vertex bone indices and weights ``(V, K)``.

    Supports K=4, K=8, or any fixed maximum influences. Unused slots use
    ``UNUSED_BONE_INDEX`` with weight 0.
    """

    joint_indices: Int32Array
    joint_weights: Float32Array
    max_influences: int = DEFAULT_MAX_INFLUENCES

    def __post_init__(self) -> None:
        idx = np.asarray(self.joint_indices, dtype=np.int32).copy()
        w = np.asarray(self.joint_weights, dtype=np.float32).copy()
        if idx.ndim != 2 or w.ndim != 2:
            raise ValueError("joint_indices and joint_weights must be 2D (V, K)")
        if idx.shape != w.shape:
            raise ValueError("joint_indices / joint_weights shape mismatch")
        object.__setattr__(self, "joint_indices", idx)
        object.__setattr__(self, "joint_weights", w)
        object.__setattr__(self, "max_influences", int(idx.shape[1]))

    @property
    def vertex_count(self) -> int:
        return int(self.joint_indices.shape[0])

    @property
    def influence_counts(self) -> Int32Array:
        return influence_counts(self.joint_indices, self.joint_weights)

    @classmethod
    def empty(cls, vertex_count: int, max_influences: int = DEFAULT_MAX_INFLUENCES) -> WeightTable:
        """Zero weights / unused indices for ``vertex_count`` vertices."""
        return cls(
            joint_indices=np.full((vertex_count, max_influences), UNUSED_BONE_INDEX, dtype=np.int32),
            joint_weights=np.zeros((vertex_count, max_influences), dtype=np.float32),
            max_influences=max_influences,
        )

    @classmethod
    def from_arrays(
        cls,
        indices: np.ndarray,
        weights: np.ndarray,
        *,
        max_influences: int | None = None,
    ) -> WeightTable:
        """Build from raw arrays (copied)."""
        idx = np.asarray(indices, dtype=np.int32)
        w = np.asarray(weights, dtype=np.float32)
        k = max_influences if max_influences is not None else int(idx.shape[1])
        if idx.shape[1] != k:
            # truncate or pad
            out_i = np.full((idx.shape[0], k), UNUSED_BONE_INDEX, dtype=np.int32)
            out_w = np.zeros((idx.shape[0], k), dtype=np.float32)
            take = min(k, idx.shape[1])
            out_i[:, :take] = idx[:, :take]
            out_w[:, :take] = w[:, :take]
            idx, w = out_i, out_w
        return cls(joint_indices=idx, joint_weights=w, max_influences=k)

    def clone(self) -> WeightTable:
        """Independently owned copy."""
        return WeightTable(
            joint_indices=self.joint_indices.copy(),
            joint_weights=self.joint_weights.copy(),
            max_influences=self.max_influences,
        )


__all__ = ["WeightTable"]
