"""Time-normalize a gait-cycle window to a fixed gait-phase grid."""

from __future__ import annotations

import numpy as np

from .catalog import NORMALIZED_POINTS


def _to_nx3(arr: np.ndarray) -> np.ndarray:
    arr = np.asarray(arr, dtype=float)
    if arr.ndim != 2:
        raise ValueError(f"expected 2D array, got {arr.shape}")
    if arr.shape[1] == 3:
        return arr
    if arr.shape[0] == 3:
        return arr.T
    raise ValueError(f"expected Nx3 or 3xN, got {arr.shape}")


def slice_cycle(arr: np.ndarray, start_frame: int, end_frame: int) -> np.ndarray:
    """Inclusive MATLAB 1-based window → ndarray (n_samples, 3)."""
    data = _to_nx3(arr)
    i0 = start_frame - 1
    i1 = end_frame - 1
    if i0 < 0 or i1 >= data.shape[0] or i1 < i0:
        raise IndexError(f"cycle window [{start_frame}, {end_frame}] outside 1..{data.shape[0]}")
    return data[i0 : i1 + 1]


def interpolate_columns(segment: np.ndarray, n_points: int = NORMALIZED_POINTS) -> np.ndarray | None:
    """Linear interpolation to n_points. Returns None if a column has <2 finite samples."""
    n = segment.shape[0]
    if n < 2:
        return None
    t_src = np.linspace(0.0, 1.0, n)
    t_dst = np.linspace(0.0, 1.0, n_points)
    out = np.empty((n_points, segment.shape[1]), dtype=np.float32)
    for j in range(segment.shape[1]):
        col = segment[:, j]
        finite = np.isfinite(col)
        if finite.sum() < 2:
            return None
        out[:, j] = np.interp(t_dst, t_src[finite], col[finite])
    return out


def normalize_signal(arr: np.ndarray, start_frame: int, end_frame: int, n_points: int = NORMALIZED_POINTS) -> np.ndarray | None:
    segment = slice_cycle(arr, start_frame, end_frame)
    return interpolate_columns(segment, n_points)


def window_finite_ratio(arr: np.ndarray | None, start_frame: int, end_frame: int) -> float | None:
    if arr is None:
        return None
    try:
        segment = slice_cycle(arr, start_frame, end_frame)
    except (IndexError, ValueError):
        return None
    if segment.size == 0:
        return None
    return float(np.isfinite(segment).mean())
