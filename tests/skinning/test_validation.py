"""Weight validation tests."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.skinning import WeightTable, validate_weight_table


def test_bad_bone() -> None:
    t = WeightTable.from_arrays(
        np.array([[0, 99, -1, -1]], np.int32),
        np.array([[0.5, 0.5, 0, 0]], np.float32),
    )
    r = validate_weight_table(t, bone_count=2)
    assert not r.ok
    assert any(i.code == "SKIN_BAD_BONE" for i in r.errors)


def test_negative_weight() -> None:
    t = WeightTable.from_arrays(
        np.array([[0, 1, -1, -1]], np.int32),
        np.array([[1.5, -0.5, 0, 0]], np.float32),
    )
    r = validate_weight_table(t, bone_count=2)
    assert any(i.code == "SKIN_NEG_WEIGHT" for i in r.errors)


def test_ok(skin) -> None:
    r = validate_weight_table(skin.weight_table, bone_count=2, vertex_count=5)
    assert r.ok
