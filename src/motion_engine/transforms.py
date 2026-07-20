"""
Rigid-body and array layout transforms for Human Reconstruction.

Status
------
Interface / placeholder. Layout normalization used by SkeletonBuilder currently
lives in :mod:`motion_engine.skeleton`. Extract shared helpers here when a
second consumer appears (export, IK, visualization).
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.floating[Any]]


def normalize_trajectory_to_n_by_3(
    coordinates: FloatArray,
    layout: str | None,
) -> FloatArray:
    """Return an ``(N, 3)`` view/copy of trajectory coordinates.

    TODO: Move the production implementation from skeleton.py here and share
    with exporters.
    """
    raise NotImplementedError(
        "normalize_trajectory_to_n_by_3 will be extracted from skeleton.py"
    )


def apply_rigid_transform(
    points: FloatArray,
    rotation: FloatArray,
    translation: FloatArray,
) -> FloatArray:
    """Apply ``R @ p + t`` to each point.

    TODO: Implement for export/retargeting pipelines.
    """
    raise NotImplementedError("apply_rigid_transform is not implemented yet.")
