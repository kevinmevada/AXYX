"""Shared types for the M3 bind-pose runtime."""

from __future__ import annotations

from enum import Enum
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

Mat4: TypeAlias = NDArray[np.float64]
Vec3: TypeAlias = NDArray[np.float64]
Quat: TypeAlias = NDArray[np.float64]


class PoseKind(str, Enum):
    """Discriminates runtime pose specializations."""

    BIND = "bind"
    REST = "rest"
    ANIMATION = "animation"
    CUSTOM = "custom"


class RestPoseKind(str, Enum):
    """Canonical rest / bind style without changing architecture."""

    IMPORTED = "imported"
    T_POSE = "t_pose"
    A_POSE = "a_pose"
    CUSTOM = "custom"


class Handedness(str, Enum):
    """Coordinate frame chirality."""

    RIGHT = "right"
    LEFT = "left"
    UNKNOWN = "unknown"


class ValidationSeverity(str, Enum):
    """Severity of a pose validation finding."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


__all__ = [
    "Mat4",
    "Vec3",
    "Quat",
    "PoseKind",
    "RestPoseKind",
    "Handedness",
    "ValidationSeverity",
]
