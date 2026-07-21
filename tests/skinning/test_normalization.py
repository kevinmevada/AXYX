"""Normalization tests."""

from __future__ import annotations

import numpy as np
import pytest

from motion_engine.rendering.avatar.skinning import (
    NormalizationMode,
    SkinningValidationError,
    WeightTable,
    normalize_weights,
)


def test_automatic_normalize() -> None:
    t = WeightTable.from_arrays(
        np.array([[0, 1, -1, -1]], np.int32),
        np.array([[2.0, 2.0, 0, 0]], np.float32),
    )
    n = normalize_weights(t, mode=NormalizationMode.AUTOMATIC)
    assert n.joint_weights[0, :2].sum() == pytest.approx(1.0)


def test_strict_raises() -> None:
    t = WeightTable.from_arrays(
        np.array([[0, 1, -1, -1]], np.int32),
        np.array([[2.0, 2.0, 0, 0]], np.float32),
    )
    with pytest.raises(SkinningValidationError):
        normalize_weights(t, mode=NormalizationMode.STRICT)


def test_preserve() -> None:
    t = WeightTable.from_arrays(
        np.array([[0, -1, -1, -1]], np.int32),
        np.array([[0.5, 0, 0, 0]], np.float32),
    )
    p = normalize_weights(t, mode=NormalizationMode.PRESERVE)
    assert p.joint_weights[0, 0] == pytest.approx(0.5)
