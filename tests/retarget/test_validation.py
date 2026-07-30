from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.retarget.validation import RetargetValidator
from tests.retarget.helpers import flexed_pose, two_bone_setup


def test_validate_profile_and_pose():
    engine, ctx, source, target, bind = two_bone_setup()
    v = RetargetValidator()
    report = v.validate_profile(engine.profile, source, {b.name for b in target.bones})
    assert report.ok
    mp = flexed_pose()
    assert v.validate_motion_pose(mp).ok
    out = engine.retarget(mp, ctx)
    assert v.validate_animation_pose(out).ok
    for b in out.bones:
        n = float(np.linalg.norm(b.rotation_xyzw))
        assert abs(n - 1.0) < 1e-5
