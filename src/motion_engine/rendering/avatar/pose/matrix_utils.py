"""Matrix utilities for bind-pose mathematics."""

from __future__ import annotations

from typing import Iterable

import numpy as np

from motion_engine.rendering.avatar.pose.constants import (
    IDENTITY_QUAT_XYZW,
    MATRIX_ORTHOGONALITY_EPS,
    MATRIX_SINGULARITY_EPS,
    QUAT_UNIT_EPS,
)
from motion_engine.rendering.avatar.pose.types import Mat4, Quat, Vec3


def identity_matrix() -> Mat4:
    """Return a 4×4 identity matrix."""
    return np.eye(4, dtype=np.float64)


def is_finite(m: Mat4) -> bool:
    """True if all entries are finite."""
    return bool(np.all(np.isfinite(m)))


def determinant3(m: Mat4) -> float:
    """Determinant of the upper-left 3×3."""
    return float(np.linalg.det(np.asarray(m, dtype=np.float64)[:3, :3]))


def is_singular(m: Mat4, *, eps: float = MATRIX_SINGULARITY_EPS) -> bool:
    """True if |det(R)| is near zero."""
    return abs(determinant3(m)) < eps


def invert_affine(m: Mat4) -> Mat4:
    """Invert a 4×4 affine matrix."""
    return np.linalg.inv(np.asarray(m, dtype=np.float64).reshape(4, 4))


def translation_of(m: Mat4) -> Vec3:
    """Extract translation column."""
    return np.asarray(m, dtype=np.float64).reshape(4, 4)[:3, 3].copy()


def is_rotation_orthogonal(
    m: Mat4,
    *,
    eps: float = MATRIX_ORTHOGONALITY_EPS,
) -> bool:
    """True if the upper-left 3×3 is approximately orthonormal."""
    r = np.asarray(m, dtype=np.float64)[:3, :3]
    should_i = r.T @ r
    return bool(np.allclose(should_i, np.eye(3), atol=eps, rtol=0.0))


def quat_normalize(q: Iterable[float]) -> Quat:
    """Return a unit quaternion (xyzw)."""
    arr = np.asarray(tuple(q), dtype=np.float64).reshape(4)
    n = float(np.linalg.norm(arr))
    if n < 1e-15:
        return np.asarray(IDENTITY_QUAT_XYZW, dtype=np.float64)
    return arr / n


def is_unit_quat(q: Iterable[float], *, eps: float = QUAT_UNIT_EPS) -> bool:
    """True if quaternion length is approximately 1."""
    arr = np.asarray(tuple(q), dtype=np.float64).reshape(4)
    return abs(float(np.linalg.norm(arr)) - 1.0) <= eps


def quat_to_matrix(q: Iterable[float]) -> Mat4:
    """Unit quaternion (xyzw) → 4×4 rotation."""
    x, y, z, w = (float(v) for v in quat_normalize(q))
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    m = identity_matrix()
    m[0, 0] = 1.0 - 2.0 * (yy + zz)
    m[0, 1] = 2.0 * (xy - wz)
    m[0, 2] = 2.0 * (xz + wy)
    m[1, 0] = 2.0 * (xy + wz)
    m[1, 1] = 1.0 - 2.0 * (xx + zz)
    m[1, 2] = 2.0 * (yz - wx)
    m[2, 0] = 2.0 * (xz - wy)
    m[2, 1] = 2.0 * (yz + wx)
    m[2, 2] = 1.0 - 2.0 * (xx + yy)
    return m


def matrix_to_quat(m: Mat4) -> Quat:
    """Extract rotation quaternion (xyzw) from a 4×4 matrix."""
    r = np.asarray(m, dtype=np.float64)[:3, :3]
    trace = float(r[0, 0] + r[1, 1] + r[2, 2])
    if trace > 0.0:
        s = 0.5 / np.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (r[2, 1] - r[1, 2]) * s
        y = (r[0, 2] - r[2, 0]) * s
        z = (r[1, 0] - r[0, 1]) * s
    elif r[0, 0] > r[1, 1] and r[0, 0] > r[2, 2]:
        s = 2.0 * np.sqrt(1.0 + r[0, 0] - r[1, 1] - r[2, 2])
        w = (r[2, 1] - r[1, 2]) / s
        x = 0.25 * s
        y = (r[0, 1] + r[1, 0]) / s
        z = (r[0, 2] + r[2, 0]) / s
    elif r[1, 1] > r[2, 2]:
        s = 2.0 * np.sqrt(1.0 + r[1, 1] - r[0, 0] - r[2, 2])
        w = (r[0, 2] - r[2, 0]) / s
        x = (r[0, 1] + r[1, 0]) / s
        y = 0.25 * s
        z = (r[1, 2] + r[2, 1]) / s
    else:
        s = 2.0 * np.sqrt(1.0 + r[2, 2] - r[0, 0] - r[1, 1])
        w = (r[1, 0] - r[0, 1]) / s
        x = (r[0, 2] + r[2, 0]) / s
        y = (r[1, 2] + r[2, 1]) / s
        z = 0.25 * s
    return quat_normalize((x, y, z, w))


def decompose_trs(m: Mat4) -> tuple[Vec3, Quat, Vec3]:
    """Decompose affine matrix into translation, rotation (xyzw), scale."""
    mat = np.asarray(m, dtype=np.float64).reshape(4, 4)
    t = mat[:3, 3].copy()
    col0, col1, col2 = mat[:3, 0], mat[:3, 1], mat[:3, 2]
    sx = float(np.linalg.norm(col0))
    sy = float(np.linalg.norm(col1))
    sz = float(np.linalg.norm(col2))
    rot = np.column_stack(
        (
            col0 / sx if sx > 1e-15 else col0,
            col1 / sy if sy > 1e-15 else col1,
            col2 / sz if sz > 1e-15 else col2,
        )
    )
    if np.linalg.det(rot) < 0.0:
        sz = -sz
        rot[:, 2] *= -1.0
    q = matrix_to_quat(np.block([[rot, np.zeros((3, 1))], [np.zeros((1, 3)), np.ones((1, 1))]]))
    return t, q, np.asarray((sx, sy, sz), dtype=np.float64)


def compose_trs(
    translation: Iterable[float],
    rotation_xyzw: Iterable[float],
    scale: Iterable[float],
) -> Mat4:
    """Compose ``T @ R @ S``."""
    t = identity_matrix()
    x, y, z = (float(v) for v in translation)
    t[0, 3], t[1, 3], t[2, 3] = x, y, z
    s = identity_matrix()
    sx, sy, sz = (float(v) for v in scale)
    s[0, 0], s[1, 1], s[2, 2] = sx, sy, sz
    return t @ quat_to_matrix(rotation_xyzw) @ s


def matrices_close(a: Mat4, b: Mat4, *, eps: float = 1e-6) -> bool:
    """Element-wise closeness for 4×4 matrices."""
    return bool(np.allclose(a, b, atol=eps, rtol=0.0))


__all__ = [
    "identity_matrix",
    "is_finite",
    "determinant3",
    "is_singular",
    "invert_affine",
    "translation_of",
    "is_rotation_orthogonal",
    "quat_normalize",
    "is_unit_quat",
    "quat_to_matrix",
    "matrix_to_quat",
    "decompose_trs",
    "compose_trs",
    "matrices_close",
]
