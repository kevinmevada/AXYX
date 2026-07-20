"""Transform propagation tests."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.pose.matrix_utils import identity_matrix, translation_of
from motion_engine.rendering.avatar.pose.transform_propagation import (
    propagate_world_transforms,
    verify_propagation,
)


def test_propagate_chain() -> None:
    eye = identity_matrix()
    l0 = eye.copy()
    l1 = eye.copy()
    l1[0, 3] = 1.0
    l2 = eye.copy()
    l2[0, 3] = 1.0
    result = propagate_world_transforms([l0, l1, l2], [None, 0, 1])
    assert abs(translation_of(result.world_matrices[2])[0] - 2.0) < 1e-9


def test_deterministic() -> None:
    mats = [identity_matrix() for _ in range(4)]
    mats[1][1, 3] = 2.0
    parents: list[int | None] = [None, 0, 0, 2]
    a = propagate_world_transforms(mats, parents)
    b = propagate_world_transforms(mats, parents)
    for x, y in zip(a.world_matrices, b.world_matrices, strict=True):
        assert np.allclose(x, y)


def test_verify_ok() -> None:
    mats = [identity_matrix(), identity_matrix()]
    mats[1][0, 3] = 3.0
    worlds = list(propagate_world_transforms(mats, [None, 0]).world_matrices)
    assert verify_propagation(mats, worlds, [None, 0]) == []


def test_verify_detects_mismatch() -> None:
    mats = [identity_matrix(), identity_matrix()]
    mats[1][0, 3] = 1.0
    bad_world = [identity_matrix(), identity_matrix()]
    assert verify_propagation(mats, bad_world, [None, 0]) == [1]


def test_bind_pose_fk_consistent(bind_pose) -> None:
    locals_m = [b.local_matrix for b in bind_pose]
    worlds = [b.global_matrix for b in bind_pose]
    parents = [b.parent_index for b in bind_pose]
    assert verify_propagation(locals_m, worlds, parents) == []
