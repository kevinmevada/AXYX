"""Shared type aliases and enums for the M2 avatar skeleton runtime."""

from __future__ import annotations

from enum import Enum, Flag, auto
from typing import NewType, TypeAlias

import numpy as np
from numpy.typing import NDArray

BoneId = NewType("BoneId", int)
BoneIndex = NewType("BoneIndex", int)

Float64Array: TypeAlias = NDArray[np.float64]
Mat4: TypeAlias = NDArray[np.float64]  # shape (4, 4), column-major affine
Vec3: TypeAlias = NDArray[np.float64]  # shape (3,)
Quat: TypeAlias = NDArray[np.float64]  # shape (4,) as xyzw


class BoneFlag(Flag):
    """Bit flags describing bone properties."""

    NONE = 0
    ROOT = auto()
    LEAF = auto()
    HAS_INVERSE_BIND = auto()
    NON_UNIFORM_SCALE = auto()
    DETACHED = auto()
    SYNTHETIC = auto()


class CoordinateSystem(str, Enum):
    """Declared source coordinate convention for the skeleton."""

    UNKNOWN = "unknown"
    Y_UP_RIGHT = "y_up_right"
    Z_UP_RIGHT = "z_up_right"
    Y_UP_LEFT = "y_up_left"
    Z_UP_LEFT = "z_up_left"


class LengthUnit(str, Enum):
    """Linear unit of bone translations / bind matrices."""

    UNKNOWN = "unknown"
    METERS = "m"
    CENTIMETERS = "cm"
    MILLIMETERS = "mm"


class ValidationSeverity(str, Enum):
    """Severity of a validation finding."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


__all__ = [
    "BoneId",
    "BoneIndex",
    "Float64Array",
    "Mat4",
    "Vec3",
    "Quat",
    "BoneFlag",
    "CoordinateSystem",
    "LengthUnit",
    "ValidationSeverity",
]
