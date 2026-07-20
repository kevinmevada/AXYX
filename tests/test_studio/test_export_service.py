"""Tests for ExportService CSV path using a minimal skeleton stand-in."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from motion_engine.skeleton import Joint, Pose, Skeleton
from motion_engine.studio.services.export_service import ExportService, ExportServiceError
from motion_engine.studio.services.motion_service import MotionService


def _tiny_skeleton() -> Skeleton:
    poses = [
        Pose(
            frame_index=0,
            joint_positions={"Root": np.array([0.0, 0.0, 0.0])},
        ),
        Pose(
            frame_index=1,
            joint_positions={"Root": np.array([1.0, 0.0, 0.0])},
        ),
    ]
    return Skeleton(
        name="t",
        subject_id="S2",
        session_name="WU01",
        root_joint="Root",
        joints={"Root": Joint(name="Root")},
        bones={},
        poses=poses,
        n_frames=2,
        sampling_rate_hz=100.0,
    )


def test_export_csv(tmp_path: Path) -> None:
    motion = MotionService()
    motion._skeleton = _tiny_skeleton()  # noqa: SLF001 - test fixture
    service = ExportService(motion)
    out = service.export_active(tmp_path / "traj.csv", fmt="csv")
    text = out.read_text(encoding="utf-8")
    assert "frame" in text
    assert "Root_x" in text
    assert "1.0" in text


def test_export_requires_loaded_data(tmp_path: Path) -> None:
    service = ExportService(MotionService())
    try:
        service.export_active(tmp_path / "x.json", fmt="json")
        raised = False
    except ExportServiceError:
        raised = True
    assert raised
