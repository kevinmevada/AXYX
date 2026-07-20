"""Constants for the M2 avatar skeleton runtime."""

from __future__ import annotations

RUNTIME_VERSION: str = "2.0.0"
"""Semantic version of the AvatarSkeleton runtime representation."""

MAX_HIERARCHY_DEPTH: int = 256
"""Depth above which validation emits a warning (sanity bound)."""

MATRIX_SINGULARITY_EPS: float = 1e-12
"""Determinant magnitude below which a matrix is treated as singular."""

SCALE_UNIFORMITY_EPS: float = 1e-6
"""Relative epsilon for detecting non-uniform scale."""

IDENTITY_SCALE: tuple[float, float, float] = (1.0, 1.0, 1.0)
IDENTITY_TRANSLATION: tuple[float, float, float] = (0.0, 0.0, 0.0)
IDENTITY_QUAT_XYZW: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)

DEFAULT_SKELETON_NAME: str = "AvatarSkeleton"

__all__ = [
    "RUNTIME_VERSION",
    "MAX_HIERARCHY_DEPTH",
    "MATRIX_SINGULARITY_EPS",
    "SCALE_UNIFORMITY_EPS",
    "IDENTITY_SCALE",
    "IDENTITY_TRANSLATION",
    "IDENTITY_QUAT_XYZW",
    "DEFAULT_SKELETON_NAME",
]
