"""Shared helpers for M6 retarget tests."""

from __future__ import annotations

import math

from motion_engine.rendering.avatar.retarget._quat import q_axis_angle
from motion_engine.rendering.avatar.retarget.mapping_factory import test_two_bone_profile
from motion_engine.rendering.avatar.retarget.retarget_engine import RetargetEngine
from motion_engine.rendering.avatar.retarget.types import (
    AXYX_COORDS,
    JointSample,
    MotionJoint,
    MotionPose,
    MotionSkeleton,
)
from tests.skinning.helpers import make_bind, make_two_bone_skeleton


def two_bone_setup():
    bind = make_bind()
    target = make_two_bone_skeleton()
    source = MotionSkeleton(
        name="motion_arm",
        joints=(
            MotionJoint("root", None, 0),
            MotionJoint("forearm", "root", 1),
        ),
        coordinate_system=AXYX_COORDS,
        root="root",
    )
    engine = RetargetEngine(test_two_bone_profile())
    ctx = engine.prepare(source, target, bind)
    return engine, ctx, source, target, bind


def flexed_pose(angle_deg: float = 30.0) -> MotionPose:
    return MotionPose(
        joints={
            "root": JointSample("root", translation=(0.0, 0.0, 0.0)),
            "forearm": JointSample(
                "forearm",
                rotation_xyzw=q_axis_angle((0.0, 0.0, 1.0), math.radians(angle_deg)),
            ),
        }
    )
