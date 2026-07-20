"""Certification tests for the high-level Unreal pipeline."""

from __future__ import annotations

import numpy as np
import pytest

from motion_engine.animation_clip import AnimationClip
from motion_engine.skeleton import Bone, Joint, Pose, Skeleton
from motion_engine.unreal.pipeline import UnrealPipeline


def _skeleton() -> Skeleton:
    joints = {
        "Pelvis": Joint(name="Pelvis", parent=None, children=["Thorax"]),
        "Thorax": Joint(name="Thorax", parent="Pelvis", children=["Head"]),
        "Head": Joint(name="Head", parent="Thorax", children=[]),
    }
    bones = {
        "Pelvis_Thorax": Bone("Pelvis_Thorax", "Pelvis", "Thorax"),
        "Thorax_Head": Bone("Thorax_Head", "Thorax", "Head"),
    }
    poses = [
        Pose(
            frame_index=i,
            joint_positions={
                "Pelvis": np.array([float(i) * 100.0, 50.0, 900.0]),
                "Thorax": np.array([float(i) * 100.0, 50.0, 1000.0]),
                "Head": np.array([float(i) * 100.0, 50.0, 1100.0]),
            },
        )
        for i in range(3)
    ]
    return Skeleton(
        name="S2_WU01",
        subject_id="S2",
        session_name="WU01",
        root_joint="Pelvis",
        joints=joints,
        bones=bones,
        poses=poses,
        n_frames=3,
        sampling_rate_hz=100.0,
        coordinate_system="lab",
        units="Unknown",
    )


def test_prepare_clip_converts_coordinates_and_maps_skeleton() -> None:
    pipeline = UnrealPipeline()
    clip = pipeline.prepare_clip(AnimationClip.from_skeleton(_skeleton()))

    pelvis = clip.frames[1].transforms["pelvis"]
    assert clip.coordinate_system == "unreal"
    assert clip.units == "cm"
    assert pelvis.translation == pytest.approx((10.0, -5.0, 90.0))
    assert "head" in clip.joint_order


def test_run_exports_complete_unreal_package(tmp_path) -> None:
    out = UnrealPipeline().run(_skeleton(), output_dir=tmp_path)

    assert out.is_dir()
    assert next(out.glob("*.fbx")).exists()
    assert next(out.glob("*.anim.json")).exists()
    assert (out / "manifest.json").exists()
