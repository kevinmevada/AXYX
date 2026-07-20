"""Tests for AnimationClip."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from motion_engine.animation_clip import AnimationClip, AnimationClipError
from motion_engine.skeleton import Bone, Joint, Pose, Skeleton


def _tiny_skeleton(n_frames: int = 5) -> Skeleton:
    joints = {
        "Pelvis": Joint(name="Pelvis", parent=None, children=["Head"]),
        "Head": Joint(name="Head", parent="Pelvis", children=[]),
    }
    bones = {
        "Pelvis_Head": Bone(
            name="Pelvis_Head",
            parent_joint="Pelvis",
            child_joint="Head",
            length=200.0,
        )
    }
    poses = []
    for i in range(n_frames):
        x = float(i) * 10.0
        poses.append(
            Pose(
                frame_index=i,
                joint_positions={
                    "Pelvis": np.array([x, 0.0, 900.0], dtype=float),
                    "Head": np.array([x, 0.0, 1100.0], dtype=float),
                },
            )
        )
    return Skeleton(
        name="clip_synth",
        subject_id="S_TEST",
        session_name="WU00",
        root_joint="Pelvis",
        joints=joints,
        bones=bones,
        poses=poses,
        n_frames=n_frames,
        sampling_rate_hz=100.0,
        coordinate_system="lab",
        units="Unknown",
    )


def test_from_skeleton_basic() -> None:
    sk = _tiny_skeleton()
    clip = AnimationClip.from_skeleton(sk)
    assert clip.n_frames == 5
    assert clip.n_joints == 2
    assert clip.fps == 100.0
    assert clip.duration_sec == pytest.approx(0.04)
    assert clip.root_joint == "Pelvis"
    assert "Pelvis" in clip.joint_order
    assert clip.root_motion is not None
    assert clip.root_motion.n_frames == 5
    assert len(clip.bones) == 1
    report = clip.validate()
    assert report["errors"] == []


def test_timestamps_and_frames() -> None:
    clip = AnimationClip.from_skeleton(_tiny_skeleton(3))
    assert list(clip.timestamps) == pytest.approx([0.0, 0.01, 0.02])
    frame = clip.get_frame(1)
    assert frame.transforms["Pelvis"].translation[0] == pytest.approx(10.0)
    assert frame.transforms["Pelvis"].valid is True


def test_json_roundtrip(tmp_path: Path) -> None:
    clip = AnimationClip.from_skeleton(_tiny_skeleton())
    path = clip.save_json(tmp_path / "clip.json")
    loaded = AnimationClip.load_json(path)
    assert loaded.n_frames == clip.n_frames
    assert loaded.n_joints == clip.n_joints
    assert loaded.fps == clip.fps
    assert loaded.get_frame(2).transforms["Head"].translation[2] == pytest.approx(1100.0)
    assert loaded.root_motion is not None
    assert loaded.root_motion.translations.shape == (5, 3)


def test_empty_skeleton_raises() -> None:
    empty = Skeleton(
        name="empty",
        subject_id="S0",
        session_name="X",
        root_joint="Pelvis",
        n_frames=0,
        poses=[],
    )
    with pytest.raises(AnimationClipError):
        AnimationClip.from_skeleton(empty)


def test_root_motion_velocity() -> None:
    clip = AnimationClip.from_skeleton(_tiny_skeleton(5))
    assert clip.root_motion is not None
    # Pelvis moves +10 units/frame at 100 Hz → 1000 units/sec in X.
    assert clip.root_motion.velocities[1, 0] == pytest.approx(1000.0)
