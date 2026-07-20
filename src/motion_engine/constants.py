"""
Shared constants for the Motion Engine.

These values encode architectural contracts derived from the Motion Catalog
and ``docs/motion_database_design.md``. They must not be duplicated as
magic literals elsewhere in the package.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Units policy
# ---------------------------------------------------------------------------

UNKNOWN_UNITS: str = "Unknown"
"""Default unit string when dataset metadata does not specify physical units."""

# ---------------------------------------------------------------------------
# Trajectory / coordinate layout
# ---------------------------------------------------------------------------

COORDINATE_DIMENSION: int = 3
"""Size of the XYZ coordinate axis on trajectory arrays."""

LAYOUT_N_BY_3: str = "N,3"
"""Layout where axis 0 is time (frames) and axis 1 is XYZ."""

LAYOUT_3_BY_N: str = "3,N"
"""Layout where axis 0 is XYZ and axis 1 is time (frames)."""

VALID_TRAJECTORY_LAYOUTS: frozenset[str] = frozenset({LAYOUT_N_BY_3, LAYOUT_3_BY_N})
"""Layouts the domain model currently accepts."""

# ---------------------------------------------------------------------------
# Session classification labels (semantic only; original names preserved)
# ---------------------------------------------------------------------------

SESSION_CLASS_WALKING: str = "Walking"
SESSION_CLASS_CALIBRATION: str = "Calibration"
SESSION_CLASS_WALKING_COPY: str = "Walking Copy"
SESSION_CLASS_CALIBRATION_COPY: str = "Calibration Copy"
SESSION_CLASS_ALTERNATE_WALKING: str = "Alternate Walking"
SESSION_CLASS_UNKNOWN: str = "Unknown"

VALID_SESSION_CLASSIFICATIONS: frozenset[str] = frozenset(
    {
        SESSION_CLASS_WALKING,
        SESSION_CLASS_CALIBRATION,
        SESSION_CLASS_WALKING_COPY,
        SESSION_CLASS_CALIBRATION_COPY,
        SESSION_CLASS_ALTERNATE_WALKING,
        SESSION_CLASS_UNKNOWN,
    }
)

# ---------------------------------------------------------------------------
# Dataset / catalog defaults (informational; not used for loading here)
# ---------------------------------------------------------------------------

DEFAULT_FILTERED_DATASET_RELATIVE_PATH: str = (
    "data/processed/Data_structure_filtered.mat"
)
"""Default relative path to the filtered MATLAB dataset."""

DEFAULT_CATALOG_RELATIVE_PATH: str = "metadata/motion_catalog"
"""Default relative path to the production Motion Catalog artifacts."""

# ---------------------------------------------------------------------------
# Sampling-rate norms observed in the filtered catalog (soft expectations)
# ---------------------------------------------------------------------------

EXPECTED_VRATE_HZ: float = 100.0
"""Observed mocap / video sampling rate (Hz) in the filtered catalog."""

EXPECTED_FPRATE_HZ: float = 1000.0
"""Observed force-plate sampling rate (Hz) in the filtered catalog."""
