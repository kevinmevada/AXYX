"""Keyframe interpolation (vectors + quaternion SLERP)."""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np

from motion_engine.rendering.avatar.animation.quaternion import quat_normalize, quat_slerp
from motion_engine.rendering.avatar.animation.types import InterpolationMode, Quat, Vec3


def lerp_vec(a: Iterable[float], b: Iterable[float], t: float) -> Vec3:
    aa = np.asarray(tuple(a), dtype=np.float64)
    bb = np.asarray(tuple(b), dtype=np.float64)
    t = float(np.clip(t, 0.0, 1.0))
    return aa + t * (bb - aa)


def step_select(a: Iterable[float], b: Iterable[float], t: float) -> Vec3:
    return np.asarray(tuple(a if t < 1.0 else b), dtype=np.float64)


def cubic_hermite(
    p0: Iterable[float],
    p1: Iterable[float],
    m0: Iterable[float],
    m1: Iterable[float],
    t: float,
) -> Vec3:
    """Cubic Hermite interpolation between ``p0`` and ``p1`` with tangents."""
    t = float(np.clip(t, 0.0, 1.0))
    t2 = t * t
    t3 = t2 * t
    h00 = 2.0 * t3 - 3.0 * t2 + 1.0
    h10 = t3 - 2.0 * t2 + t
    h01 = -2.0 * t3 + 3.0 * t2
    h11 = t3 - t2
    return (
        h00 * np.asarray(tuple(p0), dtype=np.float64)
        + h10 * np.asarray(tuple(m0), dtype=np.float64)
        + h01 * np.asarray(tuple(p1), dtype=np.float64)
        + h11 * np.asarray(tuple(m1), dtype=np.float64)
    )


def catmull_rom_tangent(prev: Iterable[float], nxt: Iterable[float]) -> Vec3:
    """Finite-difference tangent for Catmull–Rom (tension 0)."""
    return 0.5 * (
        np.asarray(tuple(nxt), dtype=np.float64) - np.asarray(tuple(prev), dtype=np.float64)
    )


def interpolate_vec(
    a: Iterable[float],
    b: Iterable[float],
    t: float,
    mode: InterpolationMode,
    *,
    tangent_a: Iterable[float] | None = None,
    tangent_b: Iterable[float] | None = None,
) -> Vec3:
    if mode is InterpolationMode.STEP:
        return step_select(a, b, t)
    if mode is InterpolationMode.CUBIC:
        m0 = tangent_a if tangent_a is not None else (0.0, 0.0, 0.0)
        m1 = tangent_b if tangent_b is not None else (0.0, 0.0, 0.0)
        return cubic_hermite(a, b, m0, m1, t)
    return lerp_vec(a, b, t)


def interpolate_quat(
    a: Iterable[float],
    b: Iterable[float],
    t: float,
    mode: InterpolationMode,
) -> Quat:
    """Interpolate rotations — always quaternion space (never Euler)."""
    if mode is InterpolationMode.STEP:
        return quat_normalize(a if t < 1.0 else b)
    # LINEAR and CUBIC both use SLERP for rotations (cubic squad reserved).
    return quat_slerp(a, b, t)


def find_key_bracket(
    times: Sequence[float],
    time: float,
) -> tuple[int, int, float]:
    """Return ``(i0, i1, local_t)`` for ``time`` in a sorted key time list.

    Assumes ``times`` is non-empty and sorted ascending.
    """
    n = len(times)
    if n == 1:
        return 0, 0, 0.0
    if time <= times[0]:
        return 0, 0, 0.0
    if time >= times[-1]:
        return n - 1, n - 1, 0.0
    # Binary search for right index.
    lo, hi = 0, n - 1
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if times[mid] <= time:
            lo = mid
        else:
            hi = mid
    i0, i1 = lo, hi
    span = times[i1] - times[i0]
    local = 0.0 if span <= 1e-15 else (time - times[i0]) / span
    return i0, i1, float(local)


__all__ = [
    "lerp_vec",
    "step_select",
    "cubic_hermite",
    "catmull_rom_tangent",
    "interpolate_vec",
    "interpolate_quat",
    "find_key_bracket",
]
