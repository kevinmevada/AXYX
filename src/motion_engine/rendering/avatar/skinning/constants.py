"""Constants for the M4 skinning runtime."""

from __future__ import annotations

RUNTIME_VERSION: str = "4.0.0"
DEFAULT_MAX_INFLUENCES: int = 4
WEIGHT_SUM_EPS: float = 1e-4
WEIGHT_NONNEG_EPS: float = -1e-8
UNUSED_BONE_INDEX: int = -1

__all__ = [
    "RUNTIME_VERSION",
    "DEFAULT_MAX_INFLUENCES",
    "WEIGHT_SUM_EPS",
    "WEIGHT_NONNEG_EPS",
    "UNUSED_BONE_INDEX",
]
