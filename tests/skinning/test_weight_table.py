"""WeightTable tests."""

from __future__ import annotations

import numpy as np
import pytest

from motion_engine.rendering.avatar.skinning import WeightTable


def test_from_arrays_and_clone() -> None:
    idx = np.array([[0, 1, -1, -1]], dtype=np.int32)
    w = np.array([[0.3, 0.7, 0, 0]], dtype=np.float32)
    t = WeightTable.from_arrays(idx, w)
    assert t.vertex_count == 1
    assert t.max_influences == 4
    c = t.clone()
    assert c.joint_weights is not t.joint_weights
    c.joint_weights[0, 0] = 9
    assert t.joint_weights[0, 0] == pytest.approx(0.3)


def test_empty() -> None:
    t = WeightTable.empty(3, max_influences=8)
    assert t.joint_indices.shape == (3, 8)
