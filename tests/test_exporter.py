"""Tests for format-agnostic animation exporters."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from motion_engine.animation_clip import AnimationClip
from motion_engine.exporter import (
    AnimationJsonExporter,
    ExportFormat,
    ExporterError,
    FbxExporter,
    create_exporter,
)
from motion_engine.skeleton import Bone, Joint, Pose, Skeleton


def _clip() -> AnimationClip:
    sk = Skeleton(
        name="exp",
        subject_id="S",
        session_name="W",
        root_joint="Pelvis",
        joints={
            "Pelvis": Joint(name="Pelvis", parent=None, children=[]),
        },
        bones={},
        poses=[
            Pose(
                frame_index=0,
                joint_positions={"Pelvis": np.array([1.0, 2.0, 3.0])},
            )
        ],
        n_frames=1,
        sampling_rate_hz=50.0,
    )
    return AnimationClip.from_skeleton(sk)


def test_json_exporter(tmp_path: Path) -> None:
    clip = _clip()
    out = AnimationJsonExporter().export(clip, tmp_path / "out.json")
    assert out.exists()
    loaded = AnimationClip.load_json(out)
    assert loaded.n_frames == 1
    assert loaded.fps == 50.0


def test_create_exporter_factory() -> None:
    exp = create_exporter(ExportFormat.ANIMATION_JSON)
    assert isinstance(exp, AnimationJsonExporter)


def test_fbx_reserved() -> None:
    with pytest.raises(ExporterError):
        FbxExporter().export(_clip(), "x.fbx")
