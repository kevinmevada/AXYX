"""Rigid transform helpers for placing anatomical bone meshes."""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.floating]


def _orthonormal_basis(direction: FloatArray) -> tuple[FloatArray, FloatArray, FloatArray]:
    forward = np.asarray(direction, dtype=float)
    length = float(np.linalg.norm(forward))
    if length < 1e-9:
        forward = np.array([0.0, 0.0, 1.0], dtype=float)
        length = 1.0
    z_axis = forward / length
    up = np.array([0.0, 0.0, 1.0], dtype=float)
    if abs(float(np.dot(z_axis, up))) > 0.95:
        up = np.array([0.0, 1.0, 0.0], dtype=float)
    x_axis = np.cross(up, z_axis)
    x_norm = float(np.linalg.norm(x_axis))
    if x_norm < 1e-12:
        x_axis = np.array([1.0, 0.0, 0.0], dtype=float)
    else:
        x_axis = x_axis / x_norm
    y_axis = np.cross(z_axis, x_axis)
    return x_axis, y_axis, z_axis


def euler_xyz_matrix(degrees: tuple[float, float, float] | list[float]) -> FloatArray:
    """Intrinsic XYZ Euler rotation (degrees) → 3×3 matrix."""
    rx, ry, rz = (math.radians(float(v)) for v in degrees)
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    rx_m = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=float)
    ry_m = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=float)
    rz_m = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=float)
    return rz_m @ ry_m @ rx_m


def bone_user_matrix(
    start: FloatArray,
    end: FloatArray,
    *,
    rest_rotation: tuple[float, float, float] | list[float] = (0.0, 0.0, 0.0),
    rest_translation: tuple[float, float, float] | list[float] = (0.0, 0.0, 0.0),
    scale: float = 1.0,
    radial_scale: float = 1.0,
    min_length: float = 1.0,
) -> FloatArray:
    """4×4 user matrix placing a unit +Z bone mesh between ``start`` and ``end``.

    Mesh convention: unit length along +Z from 0→1, cross-section in XY.
    ``radial_scale`` sets world thickness; ``scale`` is an extra uniform factor
    from YAML. Rest rotation/translation correct authoring orientation.
    """
    start = np.asarray(start, dtype=float).reshape(3)
    end = np.asarray(end, dtype=float).reshape(3)
    delta = end - start
    length = float(max(np.linalg.norm(delta), min_length))
    x_axis, y_axis, z_axis = _orthonormal_basis(delta)
    rest = euler_xyz_matrix(rest_rotation)
    # Local scale: XY = thickness, Z = bone length
    s = float(scale)
    local = np.diag([radial_scale * s, radial_scale * s, length * s])
    rot = np.column_stack((x_axis, y_axis, z_axis)) @ rest
    scaled_rot = rot @ local
    translation = start + np.asarray(rest_translation, dtype=float).reshape(3)
    mat = np.eye(4, dtype=float)
    mat[:3, :3] = scaled_rot
    mat[:3, 3] = translation
    return mat
