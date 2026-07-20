"""Tests for animation / timeline / playback architecture."""

from __future__ import annotations

import numpy as np
import pytest

from motion_engine.animation import (
    DiscreteSkeletonAnimator,
    PlaybackController,
    Timeline,
)
from motion_engine.playback import PlaybackState
from motion_engine.skeleton import Joint, Pose, Skeleton


def _tiny_skeleton() -> Skeleton:
    poses = [
        Pose(
            frame_index=i,
            joint_positions={
                "Pelvis": np.array([float(i), 0.0, 0.0], dtype=float),
            },
        )
        for i in range(4)
    ]
    return Skeleton(
        name="anim",
        subject_id="S",
        session_name="W",
        root_joint="Pelvis",
        joints={"Pelvis": Joint(name="Pelvis")},
        bones={},
        poses=poses,
        n_frames=4,
        sampling_rate_hz=100.0,
    )


def test_timeline_seek_and_time() -> None:
    tl = Timeline(n_frames=100, sampling_rate_hz=100.0)
    assert tl.duration_seconds == pytest.approx(0.99)
    assert tl.seek(50) == 50
    assert tl.current_time_seconds == pytest.approx(0.5)
    assert tl.seek(-10) == 0
    assert tl.seek(999) == 99
    assert tl.seek_time(0.25) == 25


def test_playback_loop_and_reverse() -> None:
    tl = Timeline(n_frames=5, sampling_rate_hz=100.0)
    pb = PlaybackController(tl, loop=True)
    pb.play()
    assert pb.state is PlaybackState.PLAYING
    for _ in range(6):
        pb.step(1)
    assert tl.current_frame == 1  # wrapped: 0->1..->4->0->1
    pb.set_speed(-1.0)
    assert pb.reverse is True
    frame_before = tl.current_frame
    pb.step(1)
    assert tl.current_frame == (frame_before - 1) % 5
    pb.pause()
    assert pb.state is PlaybackState.PAUSED
    pb.stop()
    assert pb.state is PlaybackState.STOPPED
    assert tl.current_frame == 0


def test_playback_speed_rejects_zero() -> None:
    pb = PlaybackController(Timeline(n_frames=3))
    with pytest.raises(ValueError):
        pb.set_speed(0.0)


def test_discrete_skeleton_animator() -> None:
    sk = _tiny_skeleton()
    animator = DiscreteSkeletonAnimator(sk)
    pose = animator.pose_at(2)
    assert pose.frame_index == 2
    assert float(pose.joint_positions["Pelvis"][0]) == 2.0


def test_animation_surface_exports() -> None:
    # Timeline / PlaybackController are part of the animation architecture surface.
    assert Timeline is not None
    assert PlaybackController is not None
