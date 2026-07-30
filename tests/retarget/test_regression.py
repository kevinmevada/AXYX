from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.retarget.factory import RetargetFactory
from motion_engine.rendering.avatar.retarget.mirror import mirror_pose
from tests.retarget.helpers import flexed_pose, two_bone_setup


def test_retarget_regression_two_bone():
    engine, ctx, *_ = two_bone_setup()
    out = engine.retarget(flexed_pose(40.0), ctx)
    assert out.bone_count == 2
    for b in out.bones:
        assert np.all(np.isfinite(b.local_matrix))
        n = float(np.linalg.norm(b.rotation_xyzw))
        assert abs(n - 1.0) < 1e-5


def test_synthetic_gait_sequence():
    factory = RetargetFactory()
    skel, poses = factory.synthetic_gait(n_frames=10, fps=30.0)
    assert len(poses) == 10
    assert "Pelvis" in poses[0].joints
    mirrored = mirror_pose(poses[0])
    assert "RHip" in mirrored.joints or "LHip" in mirrored.joints


def test_engine_does_not_mutate_bind():
    engine, ctx, source, target, bind = two_bone_setup()
    before = bind.find("forearm").local_matrix.copy()
    engine.retarget(flexed_pose(20.0), ctx)
    after = bind.find("forearm").local_matrix
    assert np.allclose(before, after)
