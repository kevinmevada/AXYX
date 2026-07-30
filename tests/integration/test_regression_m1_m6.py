"""Regression — prior milestones still pass via their public APIs."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.skeleton import AvatarSkeletonFactory
from motion_engine.rendering.avatar.pose import BindPoseFactory
from motion_engine.rendering.avatar.skinning import SkinningRuntime
from motion_engine.rendering.avatar.animation import AnimationFactory, AnimationPlayer
from motion_engine.rendering.avatar.retarget import RetargetFactory
from tests.skinning.helpers import make_two_bone_skeleton, make_segment_mesh, make_mesh_skin, make_bind


def test_m2_skeleton():
    skel = make_two_bone_skeleton()
    assert skel.bone_count == 2
    assert skel.bones[0].name == "root"


def test_m3_bind_pose():
    bind = BindPoseFactory().from_skeleton(make_two_bone_skeleton())
    assert bind.bone_count == 2


def test_m4_skinning():
    bind = make_bind()
    mesh = make_segment_mesh()
    skin = make_mesh_skin(mesh)
    from motion_engine.rendering.avatar.pose.pose import AnimationPose

    pose = AnimationPose.from_pose(bind)
    out = SkinningRuntime().deform(mesh, skin, bind_pose=bind, pose=pose)
    assert np.all(np.isfinite(out.positions))


def test_m5_animation():
    bind = make_bind()
    clip = AnimationFactory().wave_clip(bind, "forearm", duration=0.5)
    player = AnimationPlayer(bind=bind)
    player.load(clip)
    pose = player.seek(0.1)
    assert pose.bone_count == 2


def test_m6_retarget():
    factory = RetargetFactory()
    skel, poses = factory.synthetic_gait(n_frames=3)
    assert len(poses) == 3
    assert "Pelvis" in poses[0].joints
