"""Retarget engine constants."""

from __future__ import annotations

RUNTIME_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"

# Quaternion format: xyzw throughout (never Euler internally).
QUAT_IDENTITY = (0.0, 0.0, 0.0, 1.0)
VEC3_ZERO = (0.0, 0.0, 0.0)
VEC3_ONE = (1.0, 1.0, 1.0)

DEFAULT_ROOT_SOURCE = "Pelvis"
DEFAULT_ROOT_TARGET = "pelvis"

# Soft tolerance for unit quaternion checks.
QUAT_NORM_TOL = 1e-5
# Soft tolerance for finite checks.
FINITE_TOL = 1e-12

# Default moving-average window for temporal smoothing.
DEFAULT_MA_WINDOW = 5

# Benchmark / research metadata keys.
META_PROFILE = "retarget_profile"
META_SOURCE_SKELETON = "source_skeleton"
META_TARGET_SKELETON = "target_skeleton"
META_SCALE_RATIO = "scale_ratio"
META_COVERAGE = "coverage"

# Built-in profile names.
PROFILE_MATLAB_METAHUMAN = "matlab_clinical_to_metahuman"
PROFILE_MATLAB_ARMY = "matlab_clinical_to_army_girl"
PROFILE_MIXAMO = "mixamo_to_metahuman"
PROFILE_IDENTITY = "identity"
PROFILE_TEST_TWO_BONE = "test_two_bone"

__all__ = [
    "RUNTIME_VERSION",
    "SCHEMA_VERSION",
    "QUAT_IDENTITY",
    "VEC3_ZERO",
    "VEC3_ONE",
    "DEFAULT_ROOT_SOURCE",
    "DEFAULT_ROOT_TARGET",
    "QUAT_NORM_TOL",
    "FINITE_TOL",
    "DEFAULT_MA_WINDOW",
    "META_PROFILE",
    "META_SOURCE_SKELETON",
    "META_TARGET_SKELETON",
    "META_SCALE_RATIO",
    "META_COVERAGE",
    "PROFILE_MATLAB_METAHUMAN",
    "PROFILE_MATLAB_ARMY",
    "PROFILE_MIXAMO",
    "PROFILE_IDENTITY",
    "PROFILE_TEST_TWO_BONE",
]
