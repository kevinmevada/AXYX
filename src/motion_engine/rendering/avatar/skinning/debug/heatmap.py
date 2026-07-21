"""Weight heatmap scalars / colors for debug visualization."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.skinning.mesh_skin import MeshSkin
from motion_engine.rendering.avatar.skinning.types import Float32Array


def weight_heatmap_scalars(skin: MeshSkin, bone_index: int) -> Float32Array:
    """Per-vertex influence weight for ``bone_index`` in ``[0, 1]``."""
    idx = skin.weight_table.joint_indices
    w = skin.weight_table.joint_weights
    out = np.zeros((skin.vertex_count,), dtype=np.float32)
    for j in range(skin.max_influences):
        mask = idx[:, j] == int(bone_index)
        out[mask] = np.maximum(out[mask], w[mask, j])
    return out


def weight_heatmap_rgb(scalars: np.ndarray) -> Float32Array:
    """Map weights to RGB: black→blue→green→yellow→red.

    0=black, 0.25=blue, 0.5=green, 0.75=yellow, 1=red.
    """
    s = np.clip(np.asarray(scalars, dtype=np.float64).ravel(), 0.0, 1.0)
    rgb = np.zeros((s.size, 3), dtype=np.float32)
    # piecewise
    for i, v in enumerate(s):
        if v <= 0.0:
            rgb[i] = (0.05, 0.05, 0.05)
        elif v < 0.25:
            t = v / 0.25
            rgb[i] = (0.0, 0.0, t)
        elif v < 0.5:
            t = (v - 0.25) / 0.25
            rgb[i] = (0.0, t, 1.0 - t)
        elif v < 0.75:
            t = (v - 0.5) / 0.25
            rgb[i] = (t, 1.0, 0.0)
        else:
            t = (v - 0.75) / 0.25
            rgb[i] = (1.0, 1.0 - t, 0.0)
    return rgb


__all__ = ["weight_heatmap_scalars", "weight_heatmap_rgb"]
