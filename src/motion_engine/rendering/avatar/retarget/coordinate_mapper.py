"""Coordinate-system conversion (handedness, up/forward axes, units)."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.retarget._quat import q_from_matrix, q_mul, q_normalize, q_to_matrix
from motion_engine.rendering.avatar.retarget.exceptions import CoordinateError
from motion_engine.rendering.avatar.retarget.types import (
    CoordinateSystem,
    ForwardAxis,
    Handedness,
    Quat,
    UpAxis,
    Vec3,
)


def _axis_vector(axis: UpAxis | ForwardAxis) -> np.ndarray:
    name = axis.value if hasattr(axis, "value") else str(axis)
    if name == "x":
        return np.array([1.0, 0.0, 0.0], dtype=np.float64)
    if name == "y":
        return np.array([0.0, 1.0, 0.0], dtype=np.float64)
    if name == "z":
        return np.array([0.0, 0.0, 1.0], dtype=np.float64)
    raise CoordinateError(f"Unknown axis: {axis}")


def _basis_matrix(cs: CoordinateSystem) -> np.ndarray:
    """Columns are world axes expressed in this coordinate system: [right, up, forward]."""
    up = _axis_vector(cs.up)
    fwd = _axis_vector(cs.forward)
    if float(np.abs(np.dot(up, fwd))) > 0.99:
        raise CoordinateError(f"Up and forward are parallel in {cs.name}")
    if cs.handedness == Handedness.RIGHT:
        right = np.cross(up, fwd)
    else:
        right = np.cross(fwd, up)
    n = float(np.linalg.norm(right))
    if n < 1e-12:
        raise CoordinateError(f"Degenerate basis for {cs.name}")
    right = right / n
    # Re-orthogonalize forward
    fwd = np.cross(right, up) if cs.handedness == Handedness.RIGHT else np.cross(up, right)
    fwd = fwd / float(np.linalg.norm(fwd))
    up = up / float(np.linalg.norm(up))
    return np.column_stack([right, up, fwd])


class CoordinateMapper:
    """Build fixed change-of-basis between two coordinate systems."""

    def __init__(self, source: CoordinateSystem, target: CoordinateSystem) -> None:
        self.source = source
        self.target = target
        src_b = _basis_matrix(source)
        dst_b = _basis_matrix(target)
        # Map vector expressed in source → target: v_t = dst_b @ src_b.T @ v_s
        # (both bases are world-aligned abstract frames)
        self._R = dst_b @ src_b.T
        # Handedness flip: if different, reflect via determinant fix
        if source.handedness != target.handedness:
            # Reflect across up axis of target
            reflect = np.eye(3)
            # Flip the right axis (column 0)
            reflect[0, 0] = -1.0
            self._R = reflect @ self._R
        self._unit_scale = float(target.units_per_meter) / float(source.units_per_meter)
        self._R_quat = q_from_matrix(self._R)

    @property
    def rotation_matrix(self) -> np.ndarray:
        return self._R.copy()

    @property
    def unit_scale(self) -> float:
        return self._unit_scale

    def map_vector(self, v: Vec3 | np.ndarray, *, apply_units: bool = True) -> Vec3:
        arr = np.asarray(v, dtype=np.float64).reshape(3)
        out = self._R @ arr
        if apply_units:
            out = out * self._unit_scale
        return (float(out[0]), float(out[1]), float(out[2]))

    def map_quat(self, q: Quat) -> Quat:
        """Change-of-basis for orientation: R * q * R^{-1}."""
        # q' = q_R * q * q_R^{-1} where q_R represents R
        from motion_engine.rendering.avatar.retarget._quat import q_conjugate

        rq = self._R_quat
        return q_normalize(q_mul(q_mul(rq, q), q_conjugate(rq)))

    def map_matrix(self, m: np.ndarray) -> np.ndarray:
        m3 = np.asarray(m, dtype=np.float64).reshape(3, 3)
        return self._R @ m3 @ self._R.T


__all__ = ["CoordinateMapper"]
