"""Linear-blend skinning utilities."""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.floating[Any]]


def linear_blend_skin(
    rest_positions: FloatArray,
    bone_matrices: FloatArray,
    inv_bind: FloatArray,
    bone_indices: NDArray[np.integer[Any]],
    bone_weights: FloatArray,
) -> FloatArray:
    """CPU LBS: rest (N,3) → skinned (N,3)."""
    rest = np.asarray(rest_positions, dtype=np.float64)
    n = rest.shape[0]
    # Palette: bone * inv_bind
    palette = bone_matrices @ inv_bind  # (B,4,4)
    out = np.zeros((n, 3), dtype=np.float64)
    ones = np.ones((n, 1), dtype=np.float64)
    rest_h = np.concatenate([rest, ones], axis=1)  # (N,4)

    max_w = bone_indices.shape[1]
    for slot in range(max_w):
        idx = bone_indices[:, slot]
        w = bone_weights[:, slot].astype(np.float64)
        if not np.any(w > 0):
            continue
        # Gather palettes
        mats = palette[idx]  # (N,4,4)
        deformed = np.einsum("nij,nj->ni", mats, rest_h)[:, :3]
        out += deformed * w[:, None]
    return out.astype(np.float32)
