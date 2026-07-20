"""Tests for MotionService."""

from __future__ import annotations

import pytest

from motion_engine.studio.services.motion_service import MotionService, MotionServiceError


@pytest.fixture(scope="module")
def service() -> MotionService:
    svc = MotionService()
    svc.load_database()
    return svc


def test_load_database_lists_subjects(service: MotionService) -> None:
    subjects = service.list_subjects()
    assert len(subjects) >= 1
    ids = {s.subject_id for s in subjects}
    assert "S2" in ids


def test_list_sessions_for_subject(service: MotionService) -> None:
    sessions = service.list_sessions("S2")
    assert sessions
    assert any(s.name == "WU01" for s in sessions)


def test_list_sessions_includes_dataset_copies(service: MotionService) -> None:
    sessions = service.list_sessions("S12")
    assert sessions
    assert any("Copy" in s.name for s in sessions)


def test_load_session_builds_skeleton_and_clip(service: MotionService) -> None:
    skeleton, clip = service.load_session("S2", "WU01")
    assert skeleton.frame_count > 0
    assert len(skeleton.joints) > 0
    assert clip is not None
    assert clip.frame_count == skeleton.frame_count


def test_requires_database() -> None:
    svc = MotionService()
    with pytest.raises(MotionServiceError):
        svc.list_subjects()
