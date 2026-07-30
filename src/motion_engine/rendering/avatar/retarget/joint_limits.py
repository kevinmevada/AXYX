"""Joint limit definitions and DOF helpers."""

from __future__ import annotations

import math

import numpy as np

from motion_engine.rendering.avatar.retarget._quat import q_normalize, q_to_matrix
from motion_engine.rendering.avatar.retarget.types import JointLimit, Quat, Vec3


def quat_to_euler_xyz(q: Quat) -> Vec3:
    """Extract XYZ Euler (radians) for limit checking only — not used for interpolation."""
    m = q_to_matrix(q)
    # XYZ intrinsic
    sy = -m[2, 0]
    cy = math.sqrt(max(0.0, 1.0 - sy * sy))
    if cy > 1e-6:
        x = math.atan2(m[2, 1], m[2, 2])
        y = math.atan2(sy, cy)
        z = math.atan2(m[1, 0], m[0, 0])
    else:
        x = math.atan2(-m[1, 2], m[1, 1])
        y = math.atan2(sy, cy)
        z = 0.0
    return (float(x), float(y), float(z))


def euler_xyz_to_quat(e: Vec3) -> Quat:
    from motion_engine.rendering.avatar.retarget._quat import q_axis_angle, q_mul

    qx = q_axis_angle((1, 0, 0), e[0])
    qy = q_axis_angle((0, 1, 0), e[1])
    qz = q_axis_angle((0, 0, 1), e[2])
    return q_normalize(q_mul(q_mul(qz, qy), qx))


def clamp_euler(e: Vec3, lim: JointLimit) -> tuple[Vec3, bool]:
    if lim.locked:
        return (0.0, 0.0, 0.0), True
    out = []
    violated = False
    for i in range(3):
        v = float(e[i])
        lo = float(lim.min_xyz[i])
        hi = float(lim.max_xyz[i])
        if v < lo:
            v = lo
            violated = True
        elif v > hi:
            v = hi
            violated = True
        out.append(v)
    return (out[0], out[1], out[2]), violated


__all__ = ["quat_to_euler_xyz", "euler_xyz_to_quat", "clamp_euler"]
