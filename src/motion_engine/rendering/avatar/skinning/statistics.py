"""Skinning statistics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from motion_engine.rendering.avatar.skinning.weight_table import WeightTable


@dataclass(frozen=True, slots=True)
class SkinningStatistics:
    vertex_count: int
    triangle_count: int
    bone_count: int
    max_influences: int
    average_influences: float
    influence_histogram: tuple[int, ...]
    matrix_generation_ms: float = 0.0
    skinning_ms: float = 0.0
    validation_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_skinning_statistics(
    *,
    vertex_count: int,
    triangle_count: int,
    bone_count: int,
    weights: WeightTable,
    matrix_generation_ms: float = 0.0,
    skinning_ms: float = 0.0,
    validation_ms: float = 0.0,
) -> SkinningStatistics:
    counts = weights.influence_counts
    hist = [0] * (weights.max_influences + 1)
    for c in counts.tolist():
        hist[min(int(c), weights.max_influences)] += 1
    avg = float(np.mean(counts)) if counts.size else 0.0
    return SkinningStatistics(
        vertex_count=vertex_count,
        triangle_count=triangle_count,
        bone_count=bone_count,
        max_influences=weights.max_influences,
        average_influences=avg,
        influence_histogram=tuple(hist),
        matrix_generation_ms=matrix_generation_ms,
        skinning_ms=skinning_ms,
        validation_ms=validation_ms,
    )


__all__ = ["SkinningStatistics", "compute_skinning_statistics"]
