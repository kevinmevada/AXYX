"""Helpers for M5 animation tests."""

from __future__ import annotations

from motion_engine.rendering.avatar.animation import (
    AnimationFactory,
    AnimationPlayer,
    Keyframe,
    AnimationTrack,
    AnimationClip,
    TrackChannel,
    InterpolationMode,
)
from tests.skinning.helpers import make_bind, make_mesh_skin, make_segment_mesh, make_two_bone_skeleton


def make_wave_player():
    bind = make_bind()
    clip = AnimationFactory().wave_clip(bind, "forearm", duration=1.0, amplitude_deg=30.0)
    player = AnimationPlayer(bind=bind)
    player.load(clip)
    return bind, clip, player


def make_simple_rotation_clip():
    from motion_engine.rendering.avatar.animation.quaternion import quat_identity, axis_angle_quat
    import math

    q0 = quat_identity()
    q1 = axis_angle_quat((0, 0, 1), math.pi / 2)
    keys = (
        Keyframe(0.0, rotation_xyzw=tuple(float(x) for x in q0)),
        Keyframe(1.0, rotation_xyzw=tuple(float(x) for x in q1)),
    )
    track = AnimationTrack("forearm", TrackChannel.ROTATION, keys, InterpolationMode.LINEAR)
    return AnimationClip("rot", 1.0, (track,), fps=30.0)
