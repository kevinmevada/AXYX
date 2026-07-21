"""Vertex transform unit tests."""

from __future__ import annotations

import numpy as np
import pytest

from motion_engine.rendering.avatar.skinning.vertex_transform import (
    blend_points,
    transform_direction,
)


def test_blend_single_bone() -> None:
    pts = np.array([[1.0, 0.0, 0.0]], dtype=np.float64)
    mats = np.eye(4, dtype=np.float64)[None, ...]
    mats[0, 0, 3] = 5.0
    idx = np.array([[0, -1, -1, -1]], dtype=np.int32)
    w = np.array([[1.0, 0, 0, 0]], dtype=np.float32)
    out = blend_points(pts, mats, idx, w)
    assert out[0, 0] == pytest.approx(6.0)


def test_transform_direction_normalizes() -> None:
    m = np.eye(4)
    m[0, 0] = 2.0
    d = transform_direction(m, [1, 0, 0])
    assert abs(np.linalg.norm(d) - 1.0) < 1e-6
