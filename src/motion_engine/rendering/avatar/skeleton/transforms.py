"""Affine TRS transforms for avatar skeleton bones.

Convention
----------
* Matrices are ``float64`` with shape ``(4, 4)``.
* Storage is **column-major affine** in the mathematical sense used by NumPy
  indexing: ``M @ v`` applies the transform to a homogeneous column vector.
* Quaternions are stored as **xyzw** and are unit-length when authored.
* Composition for FK: ``world_child = world_parent @ local_child``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from motion_engine.rendering.avatar.skeleton.constants import (
    IDENTITY_QUAT_XYZW,
    IDENTITY_SCALE,
    IDENTITY_TRANSLATION,
    MATRIX_SINGULARITY_EPS,
    SCALE_UNIFORMITY_EPS,
)
from motion_engine.rendering.avatar.skeleton.types import Mat4, Quat, Vec3


def identity_matrix() -> Mat4:
    """Return a 4×4 identity matrix."""
    return np.eye(4, dtype=np.float64)


def translation_matrix(t: Iterable[float]) -> Mat4:
    """Build a pure translation matrix from a 3-vector."""
    x, y, z = (float(v) for v in t)
    m = identity_matrix()
    m[0, 3] = x
    m[1, 3] = y
    m[2, 3] = z
    return m


def scale_matrix(s: Iterable[float]) -> Mat4:
    """Build a pure scale matrix from a 3-vector."""
    sx, sy, sz = (float(v) for v in s)
    m = identity_matrix()
    m[0, 0] = sx
    m[1, 1] = sy
    m[2, 2] = sz
    return m


def quat_normalize(q: Iterable[float]) -> Quat:
    """Return a unit quaternion (xyzw). Falls back to identity if near-zero."""
    arr = np.asarray(tuple(q), dtype=np.float64).reshape(4)
    n = float(np.linalg.norm(arr))
    if n < 1e-15:
        return np.asarray(IDENTITY_QUAT_XYZW, dtype=np.float64)
    return arr / n


def quat_to_matrix(q: Iterable[float]) -> Mat4:
    """Convert a unit quaternion (xyzw) to a 4×4 rotation matrix."""
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
    """Extract a rotation quaternion (xyzw) from the upper-left 3×3 of ``m``."""
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


def compose_matrix(
    translation: Iterable[float],
    rotation_xyzw: Iterable[float],
    scale: Iterable[float],
) -> Mat4:
    """Compose ``T @ R @ S`` as a 4×4 affine matrix."""
    return translation_matrix(translation) @ quat_to_matrix(rotation_xyzw) @ scale_matrix(scale)


def decompose_matrix(m: Mat4) -> tuple[Vec3, Quat, Vec3]:
    """Decompose an affine matrix into translation, rotation (xyzw), scale.

    Assumes no shear (or absorbs shear into rotation/scale approximately).
    """
    mat = np.asarray(m, dtype=np.float64).reshape(4, 4)
    t = mat[:3, 3].copy()
    col0 = mat[:3, 0]
    col1 = mat[:3, 1]
    col2 = mat[:3, 2]
    sx = float(np.linalg.norm(col0))
    sy = float(np.linalg.norm(col1))
    sz = float(np.linalg.norm(col2))
    # Preserve orientation: if determinant of rotation part is negative, flip one axis.
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
    q = matrix_to_quat(
        np.block([[rot, np.zeros((3, 1))], [np.zeros((1, 3)), np.ones((1, 1))]])
    )
    s = np.asarray((sx, sy, sz), dtype=np.float64)
    return t, q, s


def is_finite_matrix(m: Mat4) -> bool:
    """Return True if all entries are finite."""
    return bool(np.all(np.isfinite(m)))


def is_singular_matrix(m: Mat4, *, eps: float = MATRIX_SINGULARITY_EPS) -> bool:
    """Return True if the upper-left 3×3 has near-zero determinant."""
    det = float(np.linalg.det(np.asarray(m, dtype=np.float64)[:3, :3]))
    return abs(det) < eps


def is_uniform_scale(s: Iterable[float], *, eps: float = SCALE_UNIFORMITY_EPS) -> bool:
    """Return True if scale components are approximately equal."""
    sx, sy, sz = (abs(float(v)) for v in s)
    mean = (sx + sy + sz) / 3.0
    if mean < eps:
        return sx == sy == sz
    return (
        abs(sx - mean) <= eps * max(1.0, mean)
        and abs(sy - mean) <= eps * max(1.0, mean)
        and abs(sz - mean) <= eps * max(1.0, mean)
    )


def invert_affine(m: Mat4) -> Mat4:
    """Invert a 4×4 affine matrix; raises ``np.linalg.LinAlgError`` if singular."""
    return np.linalg.inv(np.asarray(m, dtype=np.float64))


@dataclass(frozen=True, slots=True)
class Transform:
    """Immutable TRS transform (rest / local / world factorization)."""

    translation: tuple[float, float, float] = IDENTITY_TRANSLATION
    rotation_xyzw: tuple[float, float, float, float] = IDENTITY_QUAT_XYZW
    scale: tuple[float, float, float] = IDENTITY_SCALE

    def __post_init__(self) -> None:
        q = quat_normalize(self.rotation_xyzw)
        object.__setattr__(
            self,
            "rotation_xyzw",
            (float(q[0]), float(q[1]), float(q[2]), float(q[3])),
        )
        object.__setattr__(
            self,
            "translation",
            (
                float(self.translation[0]),
                float(self.translation[1]),
                float(self.translation[2]),
            ),
        )
        object.__setattr__(
            self,
            "scale",
            (float(self.scale[0]), float(self.scale[1]), float(self.scale[2])),
        )

    @classmethod
    def identity(cls) -> Transform:
        """Return the identity transform."""
        return cls()

    @classmethod
    def from_matrix(cls, m: Mat4) -> Transform:
        """Build a Transform by decomposing ``m``."""
        t, q, s = decompose_matrix(m)
        return cls(
            translation=(float(t[0]), float(t[1]), float(t[2])),
            rotation_xyzw=(float(q[0]), float(q[1]), float(q[2]), float(q[3])),
            scale=(float(s[0]), float(s[1]), float(s[2])),
        )

    @classmethod
    def from_translation(cls, t: Iterable[float]) -> Transform:
        """Pure translation transform."""
        x, y, z = (float(v) for v in t)
        return cls(translation=(x, y, z))

    def to_matrix(self) -> Mat4:
        """Compose this TRS into a 4×4 matrix."""
        return compose_matrix(self.translation, self.rotation_xyzw, self.scale)

    def translation_vec(self) -> Vec3:
        """Return translation as a NumPy vector."""
        return np.asarray(self.translation, dtype=np.float64)

    def rotation_quat(self) -> Quat:
        """Return rotation as a NumPy quaternion (xyzw)."""
        return np.asarray(self.rotation_xyzw, dtype=np.float64)

    def scale_vec(self) -> Vec3:
        """Return scale as a NumPy vector."""
        return np.asarray(self.scale, dtype=np.float64)

    @property
    def has_non_uniform_scale(self) -> bool:
        """True when scale components differ beyond tolerance."""
        return not is_uniform_scale(self.scale)

    def compose(self, child: Transform) -> Transform:
        """Return ``self @ child`` as TRS (parent * local)."""
        return Transform.from_matrix(self.to_matrix() @ child.to_matrix())


def propagate_world(
    local_matrices: list[Mat4],
    parent_indices: list[int | None],
    *,
    topo_order: list[int],
) -> list[Mat4]:
    """Compute world matrices from local matrices using topological order.

    Args:
        local_matrices: Per-bone local matrices.
        parent_indices: Parent index or ``None`` for roots.
        topo_order: Parent-before-child indices.

    Returns:
        List of world matrices aligned with bone indices.
    """
    n = len(local_matrices)
    world: list[Mat4] = [identity_matrix() for _ in range(n)]
    for i in topo_order:
        p = parent_indices[i]
        if p is None:
            world[i] = np.asarray(local_matrices[i], dtype=np.float64).copy()
        else:
            world[i] = world[p] @ local_matrices[i]
    return world


__all__ = [
    "Transform",
    "identity_matrix",
    "translation_matrix",
    "scale_matrix",
    "quat_normalize",
    "quat_to_matrix",
    "matrix_to_quat",
    "compose_matrix",
    "decompose_matrix",
    "is_finite_matrix",
    "is_singular_matrix",
    "is_uniform_scale",
    "invert_affine",
    "propagate_world",
]
