"""Certification tests for Unreal package export."""

from __future__ import annotations

import json

from motion_engine.animation_clip import AnimationClip, AnimationFrame, JointTransform
from motion_engine.unreal.unreal_exporter import UnrealExporter


def _clip() -> AnimationClip:
    return AnimationClip(
        name="walking",
        frames=[
            AnimationFrame(
                index=0,
                time_sec=0.0,
                transforms={"pelvis": JointTransform("pelvis", (0.0, 0.0, 0.0))},
            )
        ],
        fps=60.0,
        joint_order=["pelvis"],
        root_joint="pelvis",
        coordinate_system="unreal",
        units="cm",
        metadata={"target_skeleton": "metahuman_ue5"},
    )


def test_prepare_returns_in_memory_package() -> None:
    package = UnrealExporter().prepare(_clip())

    assert package.coordinate_system == "Unreal"
    assert package.metadata["clip_name"] == "walking"
    assert package.assets["fbx_filename"].endswith(".fbx")


def test_export_clip_writes_required_package_files(tmp_path) -> None:
    out = UnrealExporter().export_clip(_clip(), tmp_path)

    assert (out / "ME_walking.fbx").exists()
    assert (out / "ME_walking.import.json").exists()
    assert (out / "ME_walking.metadata.json").exists()
    assert (out / "preview.png").exists()
    assert (out / "manifest.json").exists()


def test_import_manifest_contains_frame_timing_and_assets(tmp_path) -> None:
    out = UnrealExporter().export_clip(_clip(), tmp_path)
    manifest = json.loads((out / "ME_walking.import.json").read_text())

    assert manifest["animation_sequence"]["fps"] == 60.0
    assert manifest["animation_sequence"]["num_frames"] == 1
    assert manifest["assets"]["animation_path"].endswith("ME_walking_Anim")
