"""Tests for PlaybackService."""

from __future__ import annotations

import pytest

from motion_engine.studio.models.playback_model import PlaybackState
from motion_engine.studio.services.playback_service import PlaybackService


def test_configure_and_transport() -> None:
    service = PlaybackService()
    service.configure(frame_count=10, fps=100.0, subject_id="S2", session_name="WU01")
    assert service.model.duration_sec == pytest.approx(0.09)
    service.play()
    assert service.model.state == PlaybackState.PLAYING
    service.pause()
    assert service.model.state == PlaybackState.PAUSED
    service.next_frame()
    assert service.model.current_frame == 1
    service.previous_frame()
    assert service.model.current_frame == 0
    service.seek(5)
    assert service.model.current_frame == 5
    service.stop()
    assert service.model.state == PlaybackState.STOPPED
    assert service.model.current_frame == 0


def test_tick_advances_while_playing() -> None:
    service = PlaybackService()
    service.configure(frame_count=100, fps=100.0)
    service.play()
    changed = service.tick(0.05)
    assert changed is True
    assert service.model.current_frame > 0
