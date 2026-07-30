"""Visual / integration checks for M5 animation playback."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.animation import (
    AnimationController,
    AnimationFactory,
    AnimationPlayer,
    AnimationState,
    ControllerState,
    LoopMode,
    Transition,
    blend_poses,
)
from motion_engine.rendering.avatar.skinning import SkinningRuntime
from tests.skinning.helpers import make_bind, make_mesh_skin, make_segment_mesh


def _play_clip(name: str, **kwargs):
    bind = make_bind()
    factory = AnimationFactory()
    if name == "idle":
        clip = factory.hold_pose(bind, duration=0.5)
    else:
        clip = factory.wave_clip(bind, "forearm", name=name, duration=0.8, **kwargs)
    player = AnimationPlayer(bind=bind)
    player.load(clip)
    player.set_loop(LoopMode.LOOP)
    player.play()
    mesh = make_segment_mesh(10)
    skin = make_mesh_skin(mesh)
    rt = SkinningRuntime()
    positions = []
    for _ in range(12):
        pose = player.tick(1.0 / 30.0)
        defm = rt.deform(mesh, skin, bind_pose=bind, pose=pose)
        assert np.all(np.isfinite(defm.positions))
        positions.append(defm.positions.copy())
    return np.stack(positions)


def test_visual_idle():
    frames = _play_clip("idle")
    # Idle hold ≈ static
    assert float(np.linalg.norm(frames[-1] - frames[0])) < 1e-3


def test_visual_walk_run_jump():
    w = _play_clip("walk", amplitude_deg=20)
    r = _play_clip("run", amplitude_deg=35)
    j = _play_clip("jump", amplitude_deg=30, axis="y")
    assert float(np.linalg.norm(w[-1] - w[0])) > 1e-4
    assert float(np.linalg.norm(r[-1] - r[0])) > 1e-4
    assert float(np.linalg.norm(j[-1] - j[0])) > 1e-4


def test_visual_loop_seek_speed_reverse():
    bind = make_bind()
    clip = AnimationFactory().wave_clip(bind, "forearm", duration=1.0)
    player = AnimationPlayer(bind=bind)
    player.load(clip)
    player.set_loop(LoopMode.LOOP)
    player.set_speed(2.0)
    player.play()
    player.tick(0.6)
    player.seek(0.1)
    assert abs(player.time - 0.1) < 1e-6
    player.reverse()
    player.tick(0.05)


def test_visual_crossfade():
    bind = make_bind()
    factory = AnimationFactory()
    clips = factory.locomotion_set(bind, "forearm")
    ctrl = AnimationController(bind=bind)
    ctrl.add_state(AnimationState("idle", ControllerState.IDLE, clips["idle"]))
    ctrl.add_state(AnimationState("walk", ControllerState.WALK, clips["walk"]))
    ctrl.add_transition(Transition("idle", "walk", 0.15))
    ctrl.set_state("idle")
    a = ctrl.tick(0.0)
    b = ctrl.set_state("walk", fade=0.15)
    c = ctrl.tick(0.05)
    blend_poses(a, b, 0.5)
    assert c.bone_count == 2
