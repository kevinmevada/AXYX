"""
Shared utilities for the Motion Engine.

Pure helpers used by the parser and loader: path resolution, MATLAB unwrap
helpers, trajectory layout detection, kinematic categorization, and session
classification. No MATLAB I/O and no domain-model construction live here.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from motion_engine.constants import (
    COORDINATE_DIMENSION,
    DEFAULT_CATALOG_RELATIVE_PATH,
    DEFAULT_FILTERED_DATASET_RELATIVE_PATH,
    LAYOUT_3_BY_N,
    LAYOUT_N_BY_3,
    SESSION_CLASS_ALTERNATE_WALKING,
    SESSION_CLASS_CALIBRATION,
    SESSION_CLASS_CALIBRATION_COPY,
    SESSION_CLASS_UNKNOWN,
    SESSION_CLASS_WALKING,
    SESSION_CLASS_WALKING_COPY,
)

logger = logging.getLogger(__name__)

# Plug-in Gait style marker names observed in the Motion Catalog.
KNOWN_MARKER_NAMES: frozenset[str] = frozenset(
    {
        "LFHD",
        "RFHD",
        "LBHD",
        "RBHD",
        "C7",
        "T10",
        "CLAV",
        "STRN",
        "RBAK",
        "LSHO",
        "LUPA",
        "LELB",
        "LFRM",
        "LWRA",
        "LWRB",
        "LFIN",
        "RSHO",
        "RUPA",
        "RELB",
        "RFRM",
        "RWRA",
        "RWRB",
        "RFIN",
        "LASI",
        "RASI",
        "LPSI",
        "RPSI",
        "LTHI",
        "LKNE",
        "LANK",
        "LHEE",
        "LTOE",
        "RTHI",
        "RKNE",
        "RANK",
        "RHEE",
        "RTOE",
    }
)

SESSION_CONTAINER_SKIP_FIELDS: frozenset[str] = frozenset({"Res", "RawRes"})
"""Fields under New_Session that are not capture sessions."""

GLOBAL_DAT_SKIP_FIELDS: frozenset[str] = frozenset({"Res"})
"""Top-level Dat fields that are not subjects."""


def resolve_dataset_path(path: str | Path | None = None) -> Path:
    """Resolve a dataset path, defaulting to the filtered MATLAB file."""
    if path is None:
        candidate = Path(DEFAULT_FILTERED_DATASET_RELATIVE_PATH)
    elif path is ...:
        raise TypeError(
            "MotionDatabase().load() takes no arguments for the default dataset. "
            "Use MotionDatabase().load() or run: python run_viewer.py"
        )
    else:
        candidate = Path(path)
    return candidate.expanduser().resolve()


def resolve_catalog_path(path: str | Path | None = None) -> Path:
    """Resolve the Motion Catalog directory path."""
    if path is None:
        candidate = Path(DEFAULT_CATALOG_RELATIVE_PATH)
    else:
        candidate = Path(path)
    return candidate.expanduser().resolve()


def unwrap_matlab(node: Any) -> Any:
    """Unwrap a MATLAB ``(1, 1)`` cell/struct envelope when present.

    Leaves arrays with meaningful shape untouched so trajectory data can be
    reused without copying.
    """
    if not isinstance(node, np.ndarray):
        return node
    if node.dtype == object and node.shape == (1, 1):
        return unwrap_matlab(node[0, 0])
    if node.shape == (1, 1) and node.dtype.names is not None:
        return node[0, 0]
    if node.shape == (1, 1) and node.size == 1:
        return node[0, 0]
    return node


def matlab_scalar(value: Any) -> Any:
    """Convert a MATLAB scalar / 1-element array to a Python scalar when safe."""
    value = unwrap_matlab(value)
    if isinstance(value, np.ndarray):
        if value.dtype.names is not None:
            return value
        if value.size == 1:
            item = value.item()
            if isinstance(item, bytes):
                return item.decode("utf-8", errors="replace")
            if isinstance(item, np.bytes_):
                return item.decode("utf-8", errors="replace")
            return item
        if value.dtype.kind in {"U", "S"} and value.size >= 1:
            return str(value.flat[0])
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def detect_trajectory_layout(
    data: NDArray[Any],
    *,
    context: str = "",
    log: logging.Logger | None = None,
) -> dict[str, Any]:
    """Detect XYZ vs time axis for a 2D trajectory array.

    Coordinate axis is the dimension of size ``COORDINATE_DIMENSION`` (3).
    The remaining dimension is the frame count. Never assumes axis order.
    Ambiguous or unresolvable shapes leave ``frame_count`` / ``layout`` as None.
    """
    log = log or logger
    if data.ndim != 2:
        raise ValueError(f"Expected 2D array, got {data.ndim}D (shape={data.shape})")

    prefix = f"{context}: " if context else ""
    result: dict[str, Any] = {
        "layout": None,
        "frame_count": None,
        "coordinate_axis": None,
        "coordinate_dimensions": None,
        "shape": tuple(int(x) for x in data.shape),
    }

    dim0_is_xyz = data.shape[0] == COORDINATE_DIMENSION
    dim1_is_xyz = data.shape[1] == COORDINATE_DIMENSION

    if dim0_is_xyz and not dim1_is_xyz:
        result["layout"] = LAYOUT_3_BY_N
        result["coordinate_axis"] = 0
        result["coordinate_dimensions"] = COORDINATE_DIMENSION
        result["frame_count"] = int(data.shape[1])
        log.debug(
            "%sDetected layout (3, N): shape=%s, frames=%s",
            prefix,
            data.shape,
            result["frame_count"],
        )
        return result

    if dim1_is_xyz and not dim0_is_xyz:
        result["layout"] = LAYOUT_N_BY_3
        result["coordinate_axis"] = 1
        result["coordinate_dimensions"] = COORDINATE_DIMENSION
        result["frame_count"] = int(data.shape[0])
        log.debug(
            "%sDetected layout (N, 3): shape=%s, frames=%s",
            prefix,
            data.shape,
            result["frame_count"],
        )
        return result

    if dim0_is_xyz and dim1_is_xyz:
        log.warning(
            "%sAmbiguous trajectory shape %s: both dimensions equal %s. "
            "frame_count left as None (no guessing).",
            prefix,
            data.shape,
            COORDINATE_DIMENSION,
        )
        return result

    finite = np.isfinite(data)
    finite_ratio = float(finite.mean()) if data.size else 0.0
    sample_min = float(np.nanmin(data)) if data.size and finite.any() else None
    sample_max = float(np.nanmax(data)) if data.size and finite.any() else None
    log.warning(
        "%sCannot determine coordinate axis for shape %s "
        "(neither dimension equals %s). finite_ratio=%.4f, "
        "value_range=[%s, %s]. frame_count left as None.",
        prefix,
        data.shape,
        COORDINATE_DIMENSION,
        finite_ratio,
        sample_min,
        sample_max,
    )
    return result


def categorize_kinematic_variable(var_name: str) -> str:
    """Categorize a kinematics field name into a semantic family.

    Returns:
        One of ``markers``, ``joint_angles``, ``joint_centers``,
        ``center_of_mass``, ``segment_com``, or ``unknown``.
    """
    var_upper = var_name.upper()

    if var_upper in {"CENTREOFMASS", "CENTREOFMASSFLOOR"}:
        return "center_of_mass"
    if "COM" in var_upper:
        return "segment_com"
    if "JC" in var_upper:
        return "joint_centers"
    if "ANGLE" in var_upper:
        return "joint_angles"
    if var_upper in KNOWN_MARKER_NAMES:
        return "markers"
    return "unknown"


def classify_session_name(session_name: str) -> str:
    """Return a semantic session classification display label.

    Original session names are never renamed; this is a label only.
    Inventory is not limited to WU01-WU09.
    """
    session_lower = session_name.lower()
    is_copy = session_lower.endswith("copy") or "copy" in session_lower

    if "static" in session_lower or "calib" in session_lower:
        return (
            SESSION_CLASS_CALIBRATION_COPY if is_copy else SESSION_CLASS_CALIBRATION
        )

    stem = session_lower
    if stem.endswith("copy"):
        stem = stem[:-4]

    if stem.startswith("wk") and stem[2:].isdigit():
        return SESSION_CLASS_ALTERNATE_WALKING

    if stem.startswith("wu"):
        rest = stem[2:]
        if rest.isdigit() and len(rest) >= 2:
            return SESSION_CLASS_WALKING_COPY if is_copy else SESSION_CLASS_WALKING
        if rest.isdigit() and len(rest) == 1:
            return SESSION_CLASS_ALTERNATE_WALKING
        return SESSION_CLASS_WALKING_COPY if is_copy else SESSION_CLASS_WALKING

    return SESSION_CLASS_UNKNOWN


def load_catalog_session_classifications(
    catalog_path: str | Path | None = None,
) -> dict[str, str]:
    """Load Original Name → Classification from ``session_types.csv`` if present."""
    catalog_dir = resolve_catalog_path(catalog_path)
    csv_path = catalog_dir / "session_types.csv"
    if not csv_path.is_file():
        return {}

    mapping: dict[str, str] = {}
    try:
        import csv

        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                original = (row.get("Original Name") or row.get("original_name") or "").strip()
                classification = (
                    row.get("Classification") or row.get("classification") or ""
                ).strip()
                if original and classification:
                    mapping[original] = classification
    except OSError as exc:
        logger.warning("Failed to read session_types.csv: %s", exc)
        return {}
    return mapping
