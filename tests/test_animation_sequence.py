"""Certification tests for post-mapping Unreal AnimationSequence."""

from __future__ import annotations

import pytest

from motion_engine.animation_clip import AnimationClip, AnimationFrame, JointTransform
from motion_engine.unreal.animation_sequence import AnimationSequence


def _clip() -> AnimationClip:
    frames = [
        AnimationFrame(
            index=0,
            time_sec=0.0,
            transforms={"pelvis": JointTransform("pelvis", (0.0, 0.0, 0.0))},
        ),
        AnimationFrame(
            index=1,
            time_sec=0.5,
            transforms={"pelvis": JointTransform("pelvis", (10.0, 0.0, 0.0))},
        ),
    ]
    return AnimationClip(
        name="metahuman_walk",
        frames=frames,
        fps=2.0,
        joint_order=["pelvis"],
        root_joint="pelvis",
        coordinate_system="unreal",
        units="cm",
        metadata={"target_skeleton": "metahuman_ue5"},
    )


def test_sequence_builds_curves_and_validates() -> None:
    sequence = AnimationSequence.from_clip(_clip())

    assert sequence.validate() == []
    assert sequence.num_frames == 2
    assert sequence.duration == pytest.approx(0.5)
    assert sequence.joint_curves["pelvis"].translations[1] == (10.0, 0.0, 0.0)


def test_sequence_sampling_interpolates_translation_and_rotation() -> None:
    sequence = AnimationSequence.from_clip(_clip())
    sampled = sequence.sample(0.25)

    assert sampled.transforms["pelvis"].translation == pytest.approx((5.0, 0.0, 0.0))
    assert sampled.transforms["pelvis"].rotation == pytest.approx((0.0, 0.0, 0.0, 1.0))


def test_sequence_json_round_trip(tmp_path) -> None:
    path = tmp_path / "sequence.json"
    sequence = AnimationSequence.from_clip(_clip())
    sequence.save_json(path)

    loaded = AnimationSequence.load_json(path)
    assert loaded.name == sequence.name
    assert loaded.joints == ["pelvis"]
    assert loaded.sample(0.5).transforms["pelvis"].translation == pytest.approx(
        (10.0, 0.0, 0.0)
    )
