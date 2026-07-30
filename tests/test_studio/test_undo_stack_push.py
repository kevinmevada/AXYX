"""Tests for undo stack push on selection."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QThreadPool
from PySide6.QtWidgets import QApplication

from motion_engine.studio.controller import StudioController
from motion_engine.studio.services.analytics_service import AnalyticsService
from motion_engine.studio.services.motion_service import MotionService
from motion_engine.studio.services.playback_service import PlaybackService
from motion_engine.studio.services.project_service import ProjectService
from motion_engine.studio.services.renderer_service import NullRenderer
from motion_engine.studio.settings import StudioSettings
from motion_engine.studio.undo import StudioUndoStack

from .test_controller import FakeView


def _flush_tasks(timeout_ms: int = 120_000) -> None:
    QThreadPool.globalInstance().waitForDone(timeout_ms)
    QCoreApplication.processEvents()


def test_undo_stack_pushes_session_selection(tmp_path) -> None:
    QApplication.instance() or QApplication([])
    settings = StudioSettings(
        organization="AXYXTest",
        application=f"Undo-{tmp_path.name}",
    )
    view = FakeView()
    controller = StudioController(
        view=view,
        project_service=ProjectService(MotionService(), settings),
        motion_service=MotionService(),
        playback_service=PlaybackService(),
        analytics_service=AnalyticsService(),
        renderer=NullRenderer(),
        settings=settings,
    )
    controller._timer.stop()
    controller.undo_stack = StudioUndoStack()

    controller.open_default_dataset()
    _flush_tasks()
    controller.select_subject("S2")
    assert controller.undo_stack.can_undo()

    controller.select_session("WU01")
    _flush_tasks()
    assert controller.undo_stack.can_undo()

    controller.undo_stack.undo()
    controller.shutdown()
