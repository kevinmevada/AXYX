"""Tests for comparison, heatmap, and AI assist."""

from __future__ import annotations

import numpy as np
import pytest

from motion_engine.skeleton import Joint, Pose, Skeleton
from motion_engine.studio.models.session_model import SessionModel
from motion_engine.studio.services.ai_assist_service import AiAssistService
from motion_engine.studio.services.comparison_service import ComparisonService
from motion_engine.studio.services.heatmap_service import HeatmapService


def _skeleton(n_frames: int = 5, *, travel: float = 1.0) -> Skeleton:
    poses = []
    for i in range(n_frames):
        poses.append(
            Pose(
                frame_index=i,
                joint_positions={
                    "Root": np.array([travel * i, 0.0, 0.0]),
                    "LFoot": np.array([travel * i, 0.0, 0.1]),
                },
            )
        )
    return Skeleton(
        name="t",
        subject_id="S2",
        session_name="WU01",
        root_joint="Root",
        joints={
            "Root": Joint(name="Root"),
            "LFoot": Joint(name="LFoot", parent="Root"),
        },
        bones={},
        poses=poses,
        n_frames=n_frames,
        sampling_rate_hz=100.0,
    )


def test_heatmap_mean_speed() -> None:
    result = HeatmapService().compute(_skeleton(6, travel=2.0))
    assert result.metric == "mean_speed"
    assert result.max_value > 0
    assert len(result.joint_names) == 2
    assert max(result.normalized()) == pytest.approx(1.0)


def test_comparison_deltas() -> None:
    a = SessionModel(
        subject_id="S2",
        name="WU01",
        classification="Walking",
        frame_count=100,
        sampling_rate_hz=100.0,
        metrics={"cadence": 110.0},
    )
    b = SessionModel(
        subject_id="S2",
        name="WU02",
        classification="Walking",
        frame_count=120,
        sampling_rate_hz=100.0,
        metrics={"cadence": 118.0},
    )
    result = ComparisonService().compare(a, b)
    assert result.deltas["cadence"] == pytest.approx(8.0)
    assert result.trial_a == "S2/WU01"


def test_ai_assist_flags_missing_metrics() -> None:
    trial = SessionModel(
        subject_id="S2",
        name="WU01",
        classification="Walking",
        frame_count=2,
        sampling_rate_hz=100.0,
        metrics={},
    )
    report = AiAssistService().analyze(trial, skeleton=_skeleton(2, travel=0.0))
    codes = {f.code for f in report.findings}
    assert "missing_clinical_metrics" in codes
    assert "zero_velocity" in codes or "insufficient_frames" in codes
