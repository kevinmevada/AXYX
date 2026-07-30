"""Visual / integration checks for M6 retarget overlays and gait."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.retarget.factory import RetargetFactory
from motion_engine.rendering.avatar.retarget.mirror import mirror_pose
from motion_engine.rendering.avatar.retarget.types import RootMotionMode
from motion_engine.rendering.avatar.skinning import SkinningRuntime
from tests.retarget.helpers import flexed_pose, two_bone_setup
from tests.skinning.helpers import make_mesh_skin


def test_visual_source_target_overlay_data():
    engine, ctx, source, target, bind = two_bone_setup()
    motion = flexed_pose(25.0)
    pose = engine.retarget(motion, ctx)
    # Overlay data: source joint positions + target bone worlds
    src_pts = [
        motion.joints[n].world_position or motion.joints[n].translation
        for n in motion.names()
    ]
    tgt_pts = [b.world_position for b in pose.bones]
    assert src_pts and tgt_pts
    assert all(np.all(np.isfinite(p)) for p in src_pts)
    assert all(np.all(np.isfinite(p)) for p in tgt_pts)


def test_visual_walking_running_phases():
    factory = RetargetFactory()
    skel, walk = factory.synthetic_gait(n_frames=20, fps=30.0)
    assert walk[0].joints["LAnkle"].world_position != walk[10].joints["LAnkle"].world_position


def test_visual_mirroring_and_scale():
    factory = RetargetFactory()
    _, poses = factory.synthetic_gait(n_frames=3)
    m = mirror_pose(poses[0])
    assert m.metadata.get("mirrored") is True


def test_visual_retarget_into_skinning():
    engine, ctx, *_ = two_bone_setup()
    pose = engine.retarget(flexed_pose(15.0), ctx)
    from tests.skinning.helpers import make_segment_mesh

    mesh = make_segment_mesh()
    skin = make_mesh_skin(mesh)
    rt = SkinningRuntime()
    deformed = rt.deform(mesh, skin, bind_pose=ctx.bind, pose=pose)
    assert deformed.positions.shape[0] > 0
    assert np.all(np.isfinite(deformed.positions))


def test_visual_constraint_and_inplace_root():
    factory = RetargetFactory()
    engine, ctx, source, target, bind = two_bone_setup()
    eng = factory.engine("test_two_bone", root_mode=RootMotionMode.IN_PLACE)
    ctx2 = eng.prepare(source, target, bind)
    p1 = eng.retarget(flexed_pose(10.0), ctx2)
    p2 = eng.retarget(flexed_pose(20.0), ctx2)
    assert p1.bone_count == p2.bone_count
