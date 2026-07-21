"""Per-vertex influence helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from motion_engine.rendering.avatar.skinning.constants import UNUSED_BONE_INDEX
from motion_engine.rendering.avatar.skinning.types import Float32Array, Int32Array


@dataclass(frozen=True, slots=True)
class VertexInfluence:
    """Single bone influence on a vertex."""

    bone_index: int
    weight: float


def pack_influences(
    influences: list[list[VertexInfluence]],
    *,
    max_influences: int,
) -> tuple[Int32Array, Float32Array]:
    """Pack sparse influences into dense ``(V, K)`` index/weight tables."""
    vcount = len(influences)
    indices = np.full((vcount, max_influences), UNUSED_BONE_INDEX, dtype=np.int32)
    weights = np.zeros((vcount, max_influences), dtype=np.float32)
    for vi, infl in enumerate(influences):
        ordered = sorted(infl, key=lambda x: -x.weight)[:max_influences]
        for j, item in enumerate(ordered):
            indices[vi, j] = int(item.bone_index)
            weights[vi, j] = float(item.weight)
    return indices, weights


def influence_counts(indices: Int32Array, weights: Float32Array) -> Int32Array:
    """Count non-zero / used influences per vertex."""
    used = (indices >= 0) & (weights > 0.0)
    return used.sum(axis=1).astype(np.int32)


__all__ = ["VertexInfluence", "pack_influences", "influence_counts"]
