"""Tests for retargeting engine."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import yaml

from motion_engine.animation_clip import AnimationClip
from motion_engine.retarget import MetaHumanRetargeter, RetargetProfile
from motion_engine.skeleton import Bone, Joint, Pose, Skeleton
from motion_engine.unreal.metahuman_mapper import MetaHumanMapper


def _skeleton() -> Skeleton:
    joints = {
        "Pelvis": Joint(name="Pelvis", parent=None, children=["LHip", "Head"]),
        "LHip": Joint(name="LHip", parent="Pelvis", children=[]),
        "Head": Joint(name="Head", parent="Pelvis", children=[]),
    }
    bones = {
        "Pelvis_LHip": Bone(
            name="Pelvis_LHip", parent_joint="Pelvis", child_joint="LHip"
        ),
        "Pelvis_Head": Bone(
            name="Pelvis_Head", parent_joint="Pelvis", child_joint="Head"
        ),
    }
    poses = [
        Pose(
            frame_index=0,
            joint_positions={
                "Pelvis": np.array([0.0, 0.0, 900.0]),
                "LHip": np.array([-100.0, 0.0, 850.0]),
                "Head": np.array([0.0, 0.0, 1100.0]),
            },
        )
    ]
    return Skeleton(
        name="rt",
        subject_id="S",
        session_name="W",
        root_joint="Pelvis",
        joints=joints,
        bones=bones,
        poses=poses,
        n_frames=1,
        sampling_rate_hz=100.0,
    )


def test_profile_from_yaml(tmp_path: Path) -> None:
    path = tmp_path / "map.yaml"
    path.write_text(
        yaml.dump(
            {
                "name": "test_map",
                "source_skeleton": "src",
                "target_skeleton": "dst",
                "root_joint": {"source": "Pelvis", "target": "pelvis"},
                "joints": {"Pelvis": "pelvis", "Head": "head", "LHip": "thigh_l"},
            }
        ),
        encoding="utf-8",
    )
    profile = RetargetProfile.from_yaml(path)
    assert profile.joint_map["Head"] == "head"
    assert "thigh_l" in profile.mapped_targets()


def test_retarget_renames_joints() -> None:
    clip = AnimationClip.from_skeleton(_skeleton())
    mapping = Path("config/retarget_metahuman.yaml")
    if not mapping.is_file():
        pytest.skip("MetaHuman mapping YAML missing")
    out = MetaHumanRetargeter(mapping).retarget(clip)
    assert "pelvis" in out.joint_order
    assert "Pelvis" not in out.joint_order
    assert out.root_joint == "pelvis"
    assert out.n_frames == clip.n_frames
    assert out.metadata["retarget_profile"]


def test_metahuman_mapper_apply() -> None:
    clip = AnimationClip.from_skeleton(_skeleton())
    mapped = MetaHumanMapper().apply(clip)
    assert mapped.get_frame(0).transforms["pelvis"].valid is True
