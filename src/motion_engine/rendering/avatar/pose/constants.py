"""Constants for the M3 bind-pose runtime."""

from __future__ import annotations

RUNTIME_VERSION: str = "3.0.0"

MATRIX_ORTHOGONALITY_EPS: float = 1e-5
MATRIX_SINGULARITY_EPS: float = 1e-12
QUAT_UNIT_EPS: float = 1e-6
PROPAGATION_MATCH_EPS: float = 1e-6
DET_NEAR_ONE_EPS: float = 1e-4

IDENTITY_QUAT_XYZW: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
IDENTITY_SCALE: tuple[float, float, float] = (1.0, 1.0, 1.0)
IDENTITY_TRANSLATION: tuple[float, float, float] = (0.0, 0.0, 0.0)

DEFAULT_POSE_NAME: str = "BindPose"

__all__ = [
    "RUNTIME_VERSION",
    "MATRIX_ORTHOGONALITY_EPS",
    "MATRIX_SINGULARITY_EPS",
    "QUAT_UNIT_EPS",
    "PROPAGATION_MATCH_EPS",
    "DET_NEAR_ONE_EPS",
    "IDENTITY_QUAT_XYZW",
    "IDENTITY_SCALE",
    "IDENTITY_TRANSLATION",
    "DEFAULT_POSE_NAME",
]
