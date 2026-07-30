"""Tests for DatasetService filtering."""

from __future__ import annotations

from motion_engine.studio.models.session_model import SessionModel
from motion_engine.studio.models.subject_model import SubjectModel
from motion_engine.studio.services.dataset_service import DatasetService
from motion_engine.studio.services.motion_service import MotionService


def test_filter_subjects_favorites_and_query() -> None:
    service = DatasetService(MotionService())
    subjects = [
        SubjectModel(subject_id="S2", session_count=10, pinned=True),
        SubjectModel(subject_id="S10", session_count=5),
        SubjectModel(subject_id="S12", session_count=3),
    ]
    filtered = service.filter_subjects(
        subjects,
        "s1",
        favorites_only=True,
        favorite_ids={"S10", "S2"},
    )
    assert [s.subject_id for s in filtered] == ["S10"]


def test_filter_trials_by_classification() -> None:
    service = DatasetService(MotionService())
    trials = [
        SessionModel(subject_id="S2", name="WU01", classification="Walking"),
        SessionModel(subject_id="S2", name="WK01", classification="Alternate Walking"),
        SessionModel(subject_id="S2", name="static", classification="Calibration"),
    ]
    walking = service.filter_trials(trials, "", classification="Walking")
    assert [t.name for t in walking] == ["WU01"]
    wu = service.filter_trials(trials, "wu")
    assert [t.name for t in wu] == ["WU01"]
