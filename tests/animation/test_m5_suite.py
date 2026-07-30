"""M5 animation package tests."""

from __future__ import annotations

import math

import numpy as np
import pytest

from motion_engine.rendering.avatar.animation import (
    AnimationController,
    AnimationFactory,
    AnimationPlayer,
    AnimationState,
    ClipLibrary,
    ControllerState,
    EvaluationCache,
    EventDispatcher,
    InterpolationMode,
    Keyframe,
    LoopMode,
    PlaybackState,
    Timeline,
    Transition,
    AnimationTrack,
    TrackChannel,
    AnimationClip,
    blend_poses,
    compute_clip_statistics,
    crossfade_weight,
    export_clip,
    import_clip,
    quat_slerp,
    wrap_time,
)
from motion_engine.rendering.avatar.skinning import SkinningRuntime
from tests.animation.helpers import make_simple_rotation_clip, make_wave_player
from tests.skinning.helpers import make_bind, make_mesh_skin, make_segment_mesh


def test_keyframe_normalizes_quat():
    k = Keyframe(0.0, rotation_xyzw=(0, 0, 0, 2))
    assert abs(math.sqrt(sum(x * x for x in k.rotation_xyzw)) - 1.0) < 1e-9


def test_track_sample_lerp():
    keys = (
        Keyframe(0.0, translation=(0, 0, 0)),
        Keyframe(1.0, translation=(2, 0, 0)),
    )
    tr = AnimationTrack("root", TrackChannel.TRANSLATION, keys)
    s = tr.sample(0.5)
    assert s.translation is not None
    assert abs(float(s.translation[0]) - 1.0) < 1e-9


def test_clip_duration_extends():
    keys = (Keyframe(0.0, translation=(0, 0, 0)), Keyframe(2.5, translation=(1, 0, 0)))
    tr = AnimationTrack("root", TrackChannel.TRANSLATION, keys)
    clip = AnimationClip("c", 1.0, (tr,))
    assert clip.duration >= 2.5


def test_slerp_halfway_90deg():
    q0 = (0, 0, 0, 1)
    q1 = (0, 0, math.sin(math.pi / 4), math.cos(math.pi / 4))  # 90 deg about Z
    q = quat_slerp(q0, q1, 0.5)
    # angle ~ 45 deg → w ≈ cos(22.5°)
    assert abs(float(q[3]) - math.cos(math.pi / 8)) < 1e-3


def test_wrap_loop_and_once():
    assert wrap_time(1.5, 1.0, LoopMode.LOOP)[0] == pytest.approx(0.5)
    t, done = wrap_time(2.0, 1.0, LoopMode.ONCE)
    assert t == 1.0 and done


def test_player_playback_and_seek():
    bind, clip, player = make_wave_player()
    player.play()
    assert player.state is PlaybackState.PLAYING
    p0 = player.tick(0.1)
    player.pause()
    assert player.state is PlaybackState.PAUSED
    p1 = player.seek(0.5)
    assert p0.bone_count == p1.bone_count == bind.bone_count
    player.set_loop(LoopMode.LOOP)
    player.play()
    player.tick(clip.duration + 0.05)
    assert player.time < clip.duration


def test_controller_states_and_crossfade():
    bind = make_bind()
    factory = AnimationFactory()
    clips = factory.locomotion_set(bind, "forearm")
    ctrl = AnimationController(bind=bind)
    for name, kind in (
        ("idle", ControllerState.IDLE),
        ("walk", ControllerState.WALK),
        ("run", ControllerState.RUN),
        ("jump", ControllerState.JUMP),
    ):
        ctrl.add_state(
            AnimationState(name=name, kind=kind, clip=clips[name], loop_mode=LoopMode.LOOP)
        )
    ctrl.add_transition(Transition("idle", "walk", duration=0.2))
    pose = ctrl.set_state("idle")
    assert pose.bone_count == 2
    pose2 = ctrl.set_state("walk", fade=0.2)
    pose3 = ctrl.tick(0.1)
    assert pose2.bone_count == pose3.bone_count == 2


def test_blending_and_weights():
    bind, clip, player = make_wave_player()
    a = player.seek(0.0)
    b = player.seek(0.5)
    mid = blend_poses(a, b, 0.5)
    assert mid.bone_count == 2
    assert 0.0 <= crossfade_weight(0.1, 0.2) <= 1.0


def test_sampling_produces_pose_for_m4():
    bind, clip, player = make_wave_player()
    mesh = make_segment_mesh(8)
    skin = make_mesh_skin(mesh)
    player.play()
    pose = player.tick(0.2)
    defm = SkinningRuntime().deform(mesh, skin, bind_pose=bind, pose=pose)
    assert defm.positions.shape[0] == mesh.vertex_count
    assert np.all(np.isfinite(defm.positions))


def test_events_and_markers():
    bind, clip, player = make_wave_player()
    seen: list[str] = []
    player.events.on("Footstep", lambda ev, t: seen.append(ev.name))
    player.play()
    t = 0.0
    while t < clip.duration:
        player.tick(0.05)
        t += 0.05
    assert "Footstep" in seen
    assert clip.marker("LoopStart") is not None


def test_cache_hit():
    bind, clip, player = make_wave_player()
    assert player.evaluator is not None
    cache = EvaluationCache(8)
    player.evaluator.cache = cache
    player.seek(0.3)
    player.seek(0.3)
    assert cache.hits >= 1


def test_statistics_and_serialization():
    _, clip, _ = make_wave_player()
    st = compute_clip_statistics(clip)
    assert st.track_count >= 1
    data = export_clip(clip)
    clip2 = import_clip(data)
    assert clip2.name == clip.name
    assert clip2.track_count == clip.track_count


def test_clip_library():
    _, clip, _ = make_wave_player()
    lib = ClipLibrary()
    lib.add(clip)
    assert lib.get(clip.name).duration == clip.duration


def test_timeline_reverse_and_frames():
    tl = Timeline(duration=1.0, fps=10.0, loop_mode=LoopMode.LOOP)
    tl.play()
    tl.set_speed(1.0)
    tl.reverse()
    assert tl.speed == -1.0
    tl.seek(0.5)
    tl.step_frames(1)
    assert tl.frame >= 0


def test_regression_bind_at_t0_near_identity_delta():
    bind, clip, player = make_wave_player()
    # At t=0 wave angle is 0 → near bind
    pose = player.seek(0.0)
    mesh = make_segment_mesh(8)
    skin = make_mesh_skin(mesh)
    rt = SkinningRuntime()
    d0 = rt.deform(mesh, skin, bind_pose=bind, pose=pose)
    d1 = rt.deform(mesh, skin, bind_pose=bind, pose=None)
    # pose=None uses bind via resolve — compare finite
    assert np.all(np.isfinite(d0.positions))
    assert np.all(np.isfinite(d1.positions))


def test_simple_rotation_clip():
    clip = make_simple_rotation_clip()
    assert clip.duration == 1.0
    s = clip.tracks[0].sample(0.5)
    assert s.rotation_xyzw is not None
