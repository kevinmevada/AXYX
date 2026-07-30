from __future__ import annotations

from motion_engine.rendering.avatar.retarget.scale_mapper import ScaleMapper
from motion_engine.rendering.avatar.retarget.types import JointSample, MotionPose


def test_height_scale():
    pose = MotionPose(
        joints={
            "Pelvis": JointSample("Pelvis", world_position=(0, 0, 1.0)),
            "Head": JointSample("Head", world_position=(0, 0, 1.8)),
        }
    )
    sm = ScaleMapper()
    factors = sm.compute(pose, {"height": 1.6}, source_root="Pelvis", source_head="Head")
    assert abs(factors.height_ratio - (1.6 / 0.8)) < 1e-9
