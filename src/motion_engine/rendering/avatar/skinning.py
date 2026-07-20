"""Linear-blend skinning hooks for future MetaHuman / SMPL avatars."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Sequence

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

FloatArray = NDArray[np.floating]


@dataclass(slots=True)
class SkinningWeights:
    """Placeholder LBS weight tables (filled when digital-twin meshes land)."""

    bone_names: list[str] = field(default_factory=list)
    indices: FloatArray | None = None
    weights: FloatArray | None = None


def apply_linear_blend_skinning(
    rest_vertices: FloatArray,
    bone_matrices: Sequence[FloatArray],
    skin: SkinningWeights,
) -> FloatArray:
    """Stub LBS — returns ``rest_vertices`` until skinned assets are wired."""
    _ = bone_matrices, skin
    if skin.weights is None or skin.indices is None:
        logger.debug("LBS skipped — no skinning weights loaded")
        return np.asarray(rest_vertices, dtype=float)
    logger.warning("LBS weights present but solver not implemented yet")
    return np.asarray(rest_vertices, dtype=float)


__all__ = ["SkinningWeights", "apply_linear_blend_skinning"]
