from __future__ import annotations

from motion_engine.rendering.avatar.retarget.offset_solver import OffsetSolver
from motion_engine.rendering.avatar.retarget.types import BoneMapEntry, JointSample, MotionPose
from tests.retarget.helpers import two_bone_setup


def test_offset_solver_produces_targets():
    engine, ctx, source, target, bind = two_bone_setup()
    rest = MotionPose(
        joints={
            "root": JointSample("root"),
            "forearm": JointSample("forearm"),
        }
    )
    entries = list(ctx.active_entries)
    table = OffsetSolver().solve(entries, rest, bind)
    assert "root" in table.by_target or "forearm" in table.by_target
