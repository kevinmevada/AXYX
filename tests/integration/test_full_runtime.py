"""Integration tests — M1–M6 composed through DigitalTwinRuntime."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.runtime import RuntimeFactory, PlaybackMode
from motion_engine.rendering.avatar.skinning import SkinningRuntime
from tests.skinning.helpers import make_bind, make_mesh_skin, make_segment_mesh
from tests.retarget.helpers import flexed_pose, two_bone_setup


def test_full_runtime():
    rt = RuntimeFactory().debug()
    rep = rt.one_click(avatar="fixture", frames=15)
    assert rep.frames == 15
    assert rep.fps > 0


def test_retarget_pipeline_integration():
    engine, ctx, *_ = two_bone_setup()
    pose = engine.retarget(flexed_pose(20.0), ctx)
    mesh = make_segment_mesh()
    skin = make_mesh_skin(mesh)
    deformed = SkinningRuntime().deform(mesh, skin, bind_pose=ctx.bind, pose=pose)
    assert np.all(np.isfinite(deformed.positions))


def test_animation_pipeline_via_runtime():
    rt = RuntimeFactory().debug()
    rt.startup()
    rt.select_avatar("fixture")
    rt.set_playback_mode(PlaybackMode.ANIMATION)
    rt.prepare()
    frames = rt.run_frames(8)
    assert len(frames) == 8
    assert all(f.finite for f in frames)
    rt.shutdown()


def test_skinning_pipeline_bind_mode():
    rt = RuntimeFactory().debug()
    rt.startup()
    rt.select_avatar("fixture")
    rt.set_playback_mode(PlaybackMode.BIND)
    rt.prepare()
    fr = rt.seek(0)
    assert fr.finite
    assert fr.vertex_count > 0
    rt.shutdown()


def test_motion_to_avatar_synthetic():
    rt = RuntimeFactory().debug()
    rt.startup()
    rt.select_subject("synthetic")
    rt.select_trial("gait")
    rt.select_avatar("fixture")
    rt.select_mapping("test_two_bone")
    rt.prepare()
    frames = rt.run_frames(12)
    assert frames[-1].bone_count == 2
    rt.shutdown()


def test_database_pipeline_optional():
    """Database load is optional; missing file returns False without crash."""
    rt = RuntimeFactory().debug()
    rt.startup()
    ok = rt.load_database("does_not_exist.mat")
    assert ok is False
    rt.shutdown()
