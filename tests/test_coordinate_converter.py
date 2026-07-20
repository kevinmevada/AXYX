"""Certification tests for Unreal coordinate conversion."""

from __future__ import annotations

import numpy as np
import pytest

from motion_engine.animation_clip import AnimationClip, AnimationFrame, JointTransform, RootMotion
from motion_engine.unreal.coordinate_converter import CoordinateConverter
from motion_engine.unreal.unreal_config import UnrealConfig


def _clip() -> AnimationClip:
    frames = [
        AnimationFrame(
            index=0,
            time_sec=0.0,
            transforms={
                "Pelvis": JointTransform(
                    "Pelvis",
                    translation=(1000.0, 200.0, 300.0),
                    rotation=(0.0, 0.0, 0.0, 1.0),
                )
            },
        )
    ]
    return AnimationClip(
        name="walk",
        frames=frames,
        fps=100.0,
        joint_order=["Pelvis"],
        root_joint="Pelvis",
        root_motion=RootMotion(
            translations=np.array([[1000.0, 200.0, 300.0]]),
            headings_rad=np.array([0.0]),
            velocities=np.array([[100.0, 0.0, 0.0]]),
            root_joint="Pelvis",
        ),
        units="Unknown",
        coordinate_system="lab",
    )


def test_convert_point_uses_yaml_scale_and_handedness() -> None:
    converter = CoordinateConverter.from_config(UnrealConfig.load())

    assert converter.convert_point((1000.0, 200.0, 300.0)) == pytest.approx(
        (100.0, -20.0, 30.0)
    )


def test_convert_rotation_preserves_unit_quaternion() -> None:
    converter = CoordinateConverter.from_config(UnrealConfig.load())
    converted = converter.convert_rotation((0.0, 0.0, 0.0, 2.0))

    assert np.linalg.norm(converted) == pytest.approx(1.0)
    assert converted == pytest.approx((0.0, 0.0, 0.0, 1.0))


def test_convert_pose_and_animation_preserve_timing_and_root_motion() -> None:
    converter = CoordinateConverter.from_config(UnrealConfig.load())
    converted = converter.convert_animation(_clip())

    pelvis = converted.frames[0].transforms["Pelvis"]
    assert converted.coordinate_system == "unreal"
    assert converted.units == "cm"
    assert converted.fps == pytest.approx(100.0)
    assert pelvis.translation == pytest.approx((100.0, -20.0, 30.0))
    assert converted.root_motion is not None
    assert converted.root_motion.translations[0].tolist() == pytest.approx(
        [100.0, -20.0, 30.0]
    )
