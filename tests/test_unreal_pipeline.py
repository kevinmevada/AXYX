"""Tests for the Unreal Engine 5 integration layer."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from motion_engine.animation_clip import AnimationClip
from motion_engine.retarget import MetaHumanRetargeter
from motion_engine.skeleton import Bone, Joint, Pose, Skeleton
from motion_engine.unreal.coordinate_converter import CoordinateConverter
from motion_engine.unreal.pipeline import UnrealPipeline
from motion_engine.unreal.transform_converter import TransformConverter, compose_matrix
from motion_engine.unreal.unreal_config import UnrealConfig
from motion_engine.unreal.unreal_exporter import UnrealExporter


def _skeleton(n_frames: int = 3) -> Skeleton:
    joints = {
        "Pelvis": Joint(name="Pelvis", parent=None, children=["Head"]),
        "Head": Joint(name="Head", parent="Pelvis", children=[]),
    }
    bones = {
        "Pelvis_Head": Bone(
            name="Pelvis_Head", parent_joint="Pelvis", child_joint="Head"
        )
    }
    poses = []
    for i in range(n_frames):
        poses.append(
            Pose(
                frame_index=i,
                joint_positions={
                    "Pelvis": np.array([float(i) * 100.0, 50.0, 900.0]),
                    "Head": np.array([float(i) * 100.0, 50.0, 1100.0]),
                },
            )
        )
    return Skeleton(
        name="S2_WU01_demo",
        subject_id="S2",
        session_name="WU01",
        root_joint="Pelvis",
        joints=joints,
        bones=bones,
        poses=poses,
        n_frames=n_frames,
        sampling_rate_hz=100.0,
        units="Unknown",
        coordinate_system="lab",
    )


def test_coordinate_scale_and_handedness() -> None:
    cfg = UnrealConfig.load()
    conv = CoordinateConverter.from_config(cfg)
    # Default: mm-like → cm (×0.1), Y negated.
    x, y, z = conv.convert_point((1000.0, 200.0, 300.0))
    assert x == pytest.approx(100.0)
    assert y == pytest.approx(-20.0)
    assert z == pytest.approx(30.0)


def test_transform_matrix() -> None:
    mat = compose_matrix((1, 2, 3), (0, 0, 0, 1), (1, 1, 1))
    assert mat.shape == (4, 4)
    assert mat[0, 3] == pytest.approx(1.0)


def test_unreal_exporter_package(tmp_path: Path) -> None:
    clip = AnimationClip.from_skeleton(_skeleton())
    if Path("config/retarget_metahuman.yaml").is_file():
        clip = MetaHumanRetargeter().retarget(clip)
    package = UnrealExporter().export(clip, output_dir=tmp_path)
    assert package.is_dir()
    files = list(package.glob("*"))
    assert any(p.name.endswith(".anim.json") for p in files)
    assert any(p.name.endswith(".import.json") for p in files)
    assert (package / "hierarchy.json").exists()


def test_pipeline_end_to_end(tmp_path: Path) -> None:
    out = UnrealPipeline().run(_skeleton(), output_dir=tmp_path)
    assert out.is_dir()
    anim = next(out.glob("*.anim.json"))
    loaded = AnimationClip.load_json(anim)
    assert loaded.coordinate_system == "unreal"
    assert loaded.units == "cm"
    assert loaded.n_frames == 3
    # Scaled + remapped pelvis translation.
    pelvis = loaded.get_frame(1).transforms.get("pelvis") or loaded.get_frame(1).transforms.get(
        "Pelvis"
    )
    assert pelvis is not None
    assert pelvis.translation[0] == pytest.approx(10.0)  # 100 * 0.1


def test_deliverable_api_shape(tmp_path: Path) -> None:
    """Mission-stated API: Skeleton → Clip → Retarget → UnrealExporter."""
    skeleton = _skeleton()
    clip = AnimationClip.from_skeleton(skeleton)
    retargeted = MetaHumanRetargeter().retarget(clip)
    package = UnrealExporter().export(retargeted, output_dir=tmp_path)
    assert package.exists()
