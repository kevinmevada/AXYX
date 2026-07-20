"""Pose validation tests."""

from __future__ import annotations

import numpy as np
import pytest

from motion_engine.rendering.avatar.pose import (
    BonePose,
    PoseValidationError,
    PoseValidator,
    validate_pose,
)
from motion_engine.rendering.avatar.pose.matrix_utils import identity_matrix
from motion_engine.rendering.avatar.pose.pose import AnimationPose


def test_valid_bind(bind_pose) -> None:
    report = validate_pose(bind_pose)
    assert report.ok


def test_empty_pose() -> None:
    pose = AnimationPose(_name="e", _bones=[])
    report = PoseValidator().validate(pose)
    assert not report.ok
    assert report.errors[0].code == "POSE_EMPTY"


def test_fk_mismatch_detected() -> None:
    eye = identity_matrix()
    bad = eye.copy()
    bad[0, 3] = 99.0
    bones = [
        BonePose.from_matrices(
            bone_id=0,
            index=0,
            name="r",
            parent_index=None,
            children=(1,),
            local_matrix=eye,
            global_matrix=eye,
            inverse_bind_matrix=eye,
        ),
        BonePose.from_matrices(
            bone_id=1,
            index=1,
            name="c",
            parent_index=0,
            children=(),
            local_matrix=eye,
            global_matrix=bad,  # inconsistent
            inverse_bind_matrix=eye,
        ),
    ]
    pose = AnimationPose(_name="bad", _bones=bones)
    report = PoseValidator().validate(pose)
    assert any(i.code == "POSE_FK_MISMATCH" for i in report.errors)


def test_raise_if_invalid() -> None:
    pose = AnimationPose(_name="e", _bones=[])
    with pytest.raises(PoseValidationError):
        PoseValidator().validate(pose).raise_if_invalid()
