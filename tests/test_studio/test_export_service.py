"""Tests for ExportService."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from motion_engine.animation_clip import AnimationClip
from motion_engine.skeleton import Joint, Pose, Skeleton
from motion_engine.studio.services.export_service import ExportService, ExportServiceError


def _clip() -> AnimationClip:
    sk = Skeleton(
        name="exp",
        subject_id="S",
        session_name="W",
        root_joint="Pelvis",
        joints={"Pelvis": Joint(name="Pelvis", parent=None, children=[])},
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


def test_export_animation_json(tmp_path: Path) -> None:
    service = ExportService()
    out = service.export_animation_json(_clip(), tmp_path / "anim.json")
    assert out.exists()
    loaded = AnimationClip.load_json(out)
    assert loaded.n_frames == 1


def test_export_service_wraps_exporter_error(monkeypatch, tmp_path: Path) -> None:
    from motion_engine.exporter import ExporterError

    class _BadExporter:
        def export(self, clip: AnimationClip, path: str | Path) -> Path:
            raise ExporterError("nope")

    monkeypatch.setattr(
        "motion_engine.studio.services.export_service.create_exporter",
        lambda _fmt: _BadExporter(),
    )
    service = ExportService()
    with pytest.raises(ExportServiceError, match="nope"):
        service.export_animation_json(_clip(), tmp_path / "x.json")
