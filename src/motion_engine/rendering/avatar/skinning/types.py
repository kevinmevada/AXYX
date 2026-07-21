"""Shared types for the M4 skinning runtime."""

from __future__ import annotations

from enum import Enum
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

Float32Array: TypeAlias = NDArray[np.float32]
Float64Array: TypeAlias = NDArray[np.float64]
Int32Array: TypeAlias = NDArray[np.int32]
Mat4: TypeAlias = NDArray[np.float64]


class SkinningAlgorithm(str, Enum):
    """Pluggable skinning algorithm identifiers."""

    LINEAR_BLEND = "linear_blend"
    DUAL_QUATERNION = "dual_quaternion"
    CENTER_OF_ROTATION = "center_of_rotation"
    RESEARCH = "research"


class NormalizationMode(str, Enum):
    """How weight rows are normalized."""

    AUTOMATIC = "automatic"
    STRICT = "strict"
    PRESERVE = "preserve"


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


__all__ = [
    "Float32Array",
    "Float64Array",
    "Int32Array",
    "Mat4",
    "SkinningAlgorithm",
    "NormalizationMode",
    "ValidationSeverity",
]
