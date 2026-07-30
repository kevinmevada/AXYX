"""Quaternion helpers for animation (xyzw, never Euler interpolation)."""

from __future__ import annotations

from typing import Iterable

import numpy as np

from motion_engine.rendering.avatar.animation.constants import SLERP_DOT_THRESHOLD
from motion_engine.rendering.avatar.animation.types import Quat


def quat_identity() -> Quat:
    return np.asarray((0.0, 0.0, 0.0, 1.0), dtype=np.float64)


def quat_normalize(q: Iterable[float]) -> Quat:
    arr = np.asarray(tuple(q), dtype=np.float64).reshape(4)
    n = float(np.linalg.norm(arr))
    if n < 1e-15:
        return quat_identity()
    return arr / n


def quat_dot(a: Iterable[float], b: Iterable[float]) -> float:
    return float(np.dot(quat_normalize(a), quat_normalize(b)))


def quat_negate(q: Iterable[float]) -> Quat:
    return -quat_normalize(q)


def quat_slerp(a: Iterable[float], b: Iterable[float], t: float) -> Quat:
    """Spherical linear interpolation of unit quaternions (xyzw)."""
    qa = quat_normalize(a)
    qb = quat_normalize(b)
    t = float(np.clip(t, 0.0, 1.0))
    dot = float(np.dot(qa, qb))
    if dot < 0.0:
        qb = -qb
        dot = -dot
    if dot > SLERP_DOT_THRESHOLD:
        # Near-parallel — fall back to normalized lerp.
        out = qa + t * (qb - qa)
        return quat_normalize(out)
    theta = float(np.arccos(np.clip(dot, -1.0, 1.0)))
    sin_theta = float(np.sin(theta))
    w0 = float(np.sin((1.0 - t) * theta) / sin_theta)
    w1 = float(np.sin(t * theta) / sin_theta)
    return quat_normalize(w0 * qa + w1 * qb)


def quat_nlerp(a: Iterable[float], b: Iterable[float], t: float) -> Quat:
    """Normalized linear quaternion blend (faster, good for small angles)."""
    qa = quat_normalize(a)
    qb = quat_normalize(b)
    if float(np.dot(qa, qb)) < 0.0:
        qb = -qb
    return quat_normalize(qa + float(t) * (qb - qa))


def axis_angle_quat(axis: Iterable[float], angle_rad: float) -> Quat:
    ax = np.asarray(tuple(axis), dtype=np.float64).reshape(3)
    n = float(np.linalg.norm(ax))
    if n < 1e-15:
        return quat_identity()
    ax = ax / n
    half = 0.5 * float(angle_rad)
    s = float(np.sin(half))
    return quat_normalize((ax[0] * s, ax[1] * s, ax[2] * s, float(np.cos(half))))


__all__ = [
    "quat_identity",
    "quat_normalize",
    "quat_dot",
    "quat_negate",
    "quat_slerp",
    "quat_nlerp",
    "axis_angle_quat",
]
