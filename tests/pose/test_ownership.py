"""Regression: AnimationPose ownership isolation from BindPose."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.pose import AnimationPose, BindPoseFactory
from tests.pose.helpers import make_chain_skeleton


def test_bonepose_objects_not_shared() -> None:
    bind = BindPoseFactory().from_skeleton(make_chain_skeleton(4))
    anim = AnimationPose.from_pose(bind)
    for i in range(bind.bone_count):
        assert anim.bones[i] is not bind.bones[i]


def test_matrices_not_aliased() -> None:
    bind = BindPoseFactory().from_skeleton(make_chain_skeleton(4))
    anim = AnimationPose.from_pose(bind)
    for i in range(bind.bone_count):
        assert anim.local_transform(i) is not bind.local_transform(i)
        assert anim.world_transform(i) is not bind.world_transform(i)
        assert anim.rest_transform(i) is not bind.rest_transform(i)
        assert anim.inverse_bind(i) is not bind.inverse_bind(i)


def test_mutating_animation_leaves_bind_unchanged() -> None:
    bind = BindPoseFactory().from_skeleton(make_chain_skeleton(4))
    anim = AnimationPose.from_pose(bind)
    before = [b.global_matrix.copy() for b in bind.bones]
    for i in range(anim.bone_count):
        anim.bones[i].global_matrix[0, 3] = 999.0 + i
        anim.bones[i].local_matrix[1, 3] = -50.0
        anim.bones[i].rest_matrix[2, 3] = 7.0
        anim.bones[i].inverse_bind_matrix[0, 0] = 2.0
        anim.bones[i].metadata["mutated"] = True
    for i, m in enumerate(before):
        assert np.allclose(bind.bones[i].global_matrix, m)
        assert "mutated" not in bind.bones[i].metadata


def test_clone_metadata_independent() -> None:
    bind = BindPoseFactory().from_skeleton(make_chain_skeleton(2))
    anim = AnimationPose.from_pose(bind)
    assert anim.bones[0].metadata is not bind.bones[0].metadata
