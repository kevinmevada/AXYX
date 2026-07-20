"""BindPose core tests."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.pose import AnimationPose, BindPose, Pose, PoseKind


def test_bind_pose_is_pose(bind_pose: BindPose) -> None:
    assert isinstance(bind_pose, Pose)
    assert bind_pose.kind is PoseKind.BIND
    assert bind_pose.bone_count == 5


def test_immutable_bones(bind_pose: BindPose) -> None:
    assert isinstance(bind_pose.bones, tuple)


def test_world_positions_chain(bind_pose: BindPose) -> None:
    assert bind_pose.world_position("root") == (0.0, 0.0, 0.0)
    assert abs(bind_pose.world_position("b3")[0] - 3.0) < 1e-9


def test_ibm_inverts_rest(bind_pose: BindPose) -> None:
    for b in bind_pose:
        product = b.inverse_bind_matrix @ b.rest_matrix
        assert np.allclose(product, np.eye(4), atol=1e-5)


def test_animation_pose_from_bind(bind_pose: BindPose) -> None:
    anim = AnimationPose.from_pose(bind_pose)
    assert anim.kind is PoseKind.ANIMATION
    assert anim.bone_count == bind_pose.bone_count
    assert anim.find("root").name == "root"
