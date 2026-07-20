"""Certification tests for YAML-driven Unreal skeleton mapping."""

from __future__ import annotations

from pathlib import Path

from motion_engine.animation_clip import AnimationClip, AnimationFrame, BoneEdge, JointTransform
from motion_engine.unreal.skeleton_mapper import SkeletonMapper


def _clip() -> AnimationClip:
    frames = [
        AnimationFrame(
            index=0,
            time_sec=0.0,
            transforms={
                "Pelvis": JointTransform("Pelvis", (0.0, 0.0, 0.0)),
                "Thorax": JointTransform("Thorax", (0.0, 0.0, 40.0)),
                "Head": JointTransform("Head", (0.0, 0.0, 80.0)),
            },
        )
    ]
    return AnimationClip(
        name="mapped_walk",
        frames=frames,
        fps=60.0,
        joint_order=["Pelvis", "Thorax", "Head"],
        bones=[
            BoneEdge("Pelvis_Thorax", "Pelvis", "Thorax"),
            BoneEdge("Thorax_Head", "Thorax", "Head"),
        ],
        root_joint="Pelvis",
        coordinate_system="unreal",
        units="cm",
    )


def test_load_mapping_and_aliases() -> None:
    mapper = SkeletonMapper().load_mapping(Path("config/retarget_metahuman.yaml"))

    assert mapper.map_joint("Pelvis") == "pelvis"
    assert mapper.map_joint("hips") == "pelvis"


def test_map_pose_reports_missing_without_failing() -> None:
    mapper = SkeletonMapper().load_mapping()
    frame, result = mapper.map_pose(_clip().frames[0])

    assert "pelvis" in frame.transforms
    assert "spine_03" in frame.transforms
    assert result.mapped
    assert result.warnings


def test_map_skeleton_preserves_hierarchy_and_metadata() -> None:
    mapper = SkeletonMapper().load_mapping()
    mapped = mapper.map_skeleton(_clip())

    assert mapped.root_joint == "pelvis"
    assert "pelvis" in mapped.joint_order
    assert "head" in mapped.joint_order
    assert mapped.metadata["target_skeleton"] == "metahuman_ue5"
    assert mapper.joint_parent_map(mapped)["spine_03"] == "pelvis"
