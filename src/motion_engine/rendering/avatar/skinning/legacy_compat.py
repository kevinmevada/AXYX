"""Backward-compatible M1 stub symbols (SkinningWeights).

The former module ``avatar/skinning.py`` was superseded by this package.
These symbols remain importable from ``motion_engine.rendering.avatar.skinning``.
"""

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
    """Legacy LBS weight table placeholder (M1-era API)."""

    bone_names: list[str] = field(default_factory=list)
    indices: FloatArray | None = None
    weights: FloatArray | None = None


def apply_linear_blend_skinning(
    rest_vertices: FloatArray,
    bone_matrices: Sequence[FloatArray],
    skin: SkinningWeights,
) -> FloatArray:
    """Legacy stub — returns rest vertices when weights are absent.

    Prefer :class:`SkinningRuntime` for production LBS.
    """
    _ = bone_matrices, skin
    if skin.weights is None or skin.indices is None:
        logger.debug("LBS skipped — no skinning weights loaded")
        return np.asarray(rest_vertices, dtype=float)
    logger.warning("Legacy LBS stub: use SkinningRuntime for real deformation")
    return np.asarray(rest_vertices, dtype=float)


__all__ = ["SkinningWeights", "apply_linear_blend_skinning"]
