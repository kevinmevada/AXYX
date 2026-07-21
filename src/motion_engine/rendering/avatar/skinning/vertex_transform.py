"""Low-level vertex transform helpers for LBS."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.skinning.types import Float32Array, Float64Array, Mat4


def transform_point(matrix: Mat4, point: np.ndarray) -> Float64Array:
    """Apply affine 4×4 to a 3-vector point."""
    p = np.asarray(point, dtype=np.float64).reshape(3)
    r = matrix[:3, :3] @ p + matrix[:3, 3]
    return r


def transform_direction(matrix: Mat4, direction: np.ndarray) -> Float64Array:
    """Apply linear 3×3 part (no translation) and renormalize if non-zero."""
    d = np.asarray(direction, dtype=np.float64).reshape(3)
    r = matrix[:3, :3] @ d
    n = float(np.linalg.norm(r))
    if n > 1e-15:
        r /= n
    return r


def blend_points(
    points: np.ndarray,
    matrices: np.ndarray,
    indices: np.ndarray,
    weights: np.ndarray,
) -> Float32Array:
    """Vectorized LBS for positions.

    Args:
        points: ``(V, 3)``
        matrices: ``(B, 4, 4)`` skin matrices
        indices: ``(V, K)`` bone indices (``-1`` unused)
        weights: ``(V, K)`` weights
    """
    v = np.asarray(points, dtype=np.float64)
    vcount = v.shape[0]
    out = np.zeros((vcount, 3), dtype=np.float64)
    k = indices.shape[1]
    ones = np.ones((vcount,), dtype=np.float64)
    for j in range(k):
        idx = indices[:, j]
        w = weights[:, j].astype(np.float64)
        valid = (idx >= 0) & (w > 0.0)
        if not np.any(valid):
            continue
        # Gather matrices for valid verts — loop bones unique for speed on small B
        for bone in np.unique(idx[valid]):
            mask = valid & (idx == bone)
            m = matrices[int(bone)]
            # p' = R p + t
            transformed = (v[mask] @ m[:3, :3].T) + m[:3, 3]
            out[mask] += w[mask, None] * transformed
    return out.astype(np.float32)


def blend_directions(
    dirs: np.ndarray,
    matrices: np.ndarray,
    indices: np.ndarray,
    weights: np.ndarray,
) -> Float32Array:
    """Vectorized LBS for normals/tangents (rotation only, then normalize)."""
    d = np.asarray(dirs, dtype=np.float64)
    vcount = d.shape[0]
    out = np.zeros((vcount, 3), dtype=np.float64)
    k = indices.shape[1]
    for j in range(k):
        idx = indices[:, j]
        w = weights[:, j].astype(np.float64)
        valid = (idx >= 0) & (w > 0.0)
        if not np.any(valid):
            continue
        for bone in np.unique(idx[valid]):
            mask = valid & (idx == bone)
            m = matrices[int(bone)]
            transformed = d[mask] @ m[:3, :3].T
            out[mask] += w[mask, None] * transformed
    norms = np.linalg.norm(out, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-15)
    out /= norms
    return out.astype(np.float32)


__all__ = [
    "transform_point",
    "transform_direction",
    "blend_points",
    "blend_directions",
]
