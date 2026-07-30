"""Quaternion utilities for retarget (xyzw, never Euler)."""

from __future__ import annotations

from typing import Iterable

import numpy as np

from motion_engine.rendering.avatar.retarget.constants import QUAT_IDENTITY
from motion_engine.rendering.avatar.retarget.types import Quat, Vec3


def q_identity() -> Quat:
    return QUAT_IDENTITY


def q_normalize(q: Iterable[float]) -> Quat:
    arr = np.asarray(tuple(q), dtype=np.float64).reshape(4)
    n = float(np.linalg.norm(arr))
    if n < 1e-15:
        return QUAT_IDENTITY
    arr = arr / n
    return (float(arr[0]), float(arr[1]), float(arr[2]), float(arr[3]))


def q_mul(a: Iterable[float], b: Iterable[float]) -> Quat:
    ax, ay, az, aw = q_normalize(a)
    bx, by, bz, bw = q_normalize(b)
    return q_normalize(
        (
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz,
        )
    )


def q_conjugate(q: Iterable[float]) -> Quat:
    x, y, z, w = q_normalize(q)
    return (-x, -y, -z, w)


def q_rotate_vec(q: Iterable[float], v: Iterable[float]) -> Vec3:
    qx, qy, qz, qw = q_normalize(q)
    vx, vy, vz = (float(x) for x in v)
    # t = 2 * cross(q.xyz, v)
    tx = 2.0 * (qy * vz - qz * vy)
    ty = 2.0 * (qz * vx - qx * vz)
    tz = 2.0 * (qx * vy - qy * vx)
    # v' = v + qw * t + cross(q.xyz, t)
    return (
        vx + qw * tx + (qy * tz - qz * ty),
        vy + qw * ty + (qz * tx - qx * tz),
        vz + qw * tz + (qx * ty - qy * tx),
    )


def q_from_matrix(m: np.ndarray) -> Quat:
    """Rotation matrix (3x3) → quaternion xyzw."""
    m = np.asarray(m, dtype=np.float64).reshape(3, 3)
    trace = float(m[0, 0] + m[1, 1] + m[2, 2])
    if trace > 0.0:
        s = 0.5 / np.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (m[2, 1] - m[1, 2]) * s
        y = (m[0, 2] - m[2, 0]) * s
        z = (m[1, 0] - m[0, 1]) * s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = 2.0 * np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2])
        w = (m[2, 1] - m[1, 2]) / s
        x = 0.25 * s
        y = (m[0, 1] + m[1, 0]) / s
        z = (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = 2.0 * np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2])
        w = (m[0, 2] - m[2, 0]) / s
        x = (m[0, 1] + m[1, 0]) / s
        y = 0.25 * s
        z = (m[1, 2] + m[2, 1]) / s
    else:
        s = 2.0 * np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1])
        w = (m[1, 0] - m[0, 1]) / s
        x = (m[0, 2] + m[2, 0]) / s
        y = (m[1, 2] + m[2, 1]) / s
        z = 0.25 * s
    return q_normalize((float(x), float(y), float(z), float(w)))


def q_to_matrix(q: Iterable[float]) -> np.ndarray:
    x, y, z, w = q_normalize(q)
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return np.array(
        [
            [1 - 2 * (yy + zz), 2 * (xy - wz), 2 * (xz + wy)],
            [2 * (xy + wz), 1 - 2 * (xx + zz), 2 * (yz - wx)],
            [2 * (xz - wy), 2 * (yz + wx), 1 - 2 * (xx + yy)],
        ],
        dtype=np.float64,
    )


def q_from_to(a: Iterable[float], b: Iterable[float]) -> Quat:
    """Shortest rotation taking unit vector a → unit vector b."""
    va = np.asarray(tuple(a), dtype=np.float64).reshape(3)
    vb = np.asarray(tuple(b), dtype=np.float64).reshape(3)
    na = float(np.linalg.norm(va))
    nb = float(np.linalg.norm(vb))
    if na < 1e-15 or nb < 1e-15:
        return QUAT_IDENTITY
    va = va / na
    vb = vb / nb
    dot = float(np.clip(np.dot(va, vb), -1.0, 1.0))
    if dot > 1.0 - 1e-8:
        return QUAT_IDENTITY
    if dot < -1.0 + 1e-8:
        axis = np.cross(va, np.array([1.0, 0.0, 0.0]))
        if float(np.linalg.norm(axis)) < 1e-8:
            axis = np.cross(va, np.array([0.0, 1.0, 0.0]))
        axis = axis / np.linalg.norm(axis)
        return q_normalize((float(axis[0]), float(axis[1]), float(axis[2]), 0.0))
    axis = np.cross(va, vb)
    q = np.array([axis[0], axis[1], axis[2], 1.0 + dot], dtype=np.float64)
    return q_normalize(q)


def q_axis_angle(axis: Iterable[float], angle_rad: float) -> Quat:
    ax = np.asarray(tuple(axis), dtype=np.float64).reshape(3)
    n = float(np.linalg.norm(ax))
    if n < 1e-15:
        return QUAT_IDENTITY
    ax = ax / n
    half = 0.5 * float(angle_rad)
    s = float(np.sin(half))
    return q_normalize((ax[0] * s, ax[1] * s, ax[2] * s, float(np.cos(half))))


def q_slerp(a: Iterable[float], b: Iterable[float], t: float) -> Quat:
    qa = np.asarray(q_normalize(a), dtype=np.float64)
    qb = np.asarray(q_normalize(b), dtype=np.float64)
    t = float(np.clip(t, 0.0, 1.0))
    dot = float(np.dot(qa, qb))
    if dot < 0.0:
        qb = -qb
        dot = -dot
    if dot > 0.9995:
        return q_normalize(qa + t * (qb - qa))
    theta = float(np.arccos(np.clip(dot, -1.0, 1.0)))
    sin_t = float(np.sin(theta))
    w0 = float(np.sin((1.0 - t) * theta) / sin_t)
    w1 = float(np.sin(t * theta) / sin_t)
    return q_normalize(w0 * qa + w1 * qb)


def q_average(quats: list[Iterable[float]]) -> Quat:
    """Normalized mean of quats (hemisphere-aligned)."""
    if not quats:
        return QUAT_IDENTITY
    acc = np.zeros(4, dtype=np.float64)
    ref = np.asarray(q_normalize(quats[0]), dtype=np.float64)
    for q in quats:
        v = np.asarray(q_normalize(q), dtype=np.float64)
        if float(np.dot(v, ref)) < 0.0:
            v = -v
        acc += v
    return q_normalize(acc)


def swing_twist_decompose(q: Iterable[float], twist_axis: Iterable[float]) -> tuple[Quat, Quat]:
    """Decompose q into swing * twist about twist_axis."""
    qa = q_normalize(q)
    ax = np.asarray(tuple(twist_axis), dtype=np.float64).reshape(3)
    n = float(np.linalg.norm(ax))
    if n < 1e-15:
        return QUAT_IDENTITY, qa
    ax = ax / n
    # twist = projection of quat vector part onto axis
    qx, qy, qz, qw = qa
    proj = qx * ax[0] + qy * ax[1] + qz * ax[2]
    twist = q_normalize((ax[0] * proj, ax[1] * proj, ax[2] * proj, qw))
    swing = q_mul(qa, q_conjugate(twist))
    return swing, twist


__all__ = [
    "q_identity",
    "q_normalize",
    "q_mul",
    "q_conjugate",
    "q_rotate_vec",
    "q_from_matrix",
    "q_to_matrix",
    "q_from_to",
    "q_axis_angle",
    "q_slerp",
    "q_average",
    "swing_twist_decompose",
]
