"""Tests for MainWindow construction."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from motion_engine.studio.main_window import MainWindow
from motion_engine.studio.settings import StudioSettings
from motion_engine.studio.widgets.status_bar import StatusSnapshot


def test_main_window_builds_and_updates_status() -> None:
    QApplication.instance() or QApplication([])
    settings = StudioSettings(
        organization="AXYXTest",
        application="MainWindowSmoke",
    )
    window = MainWindow(settings)
    window.show_welcome(True)
    assert window._stack.currentWidget() is window.welcome
    window.show_welcome(False)
    assert window._stack.currentWidget() is window._workspace
    window.update_status(
        StatusSnapshot(dataset="x.mat", subject="S2", session="WU01", frames=10)
    )
    assert "S2" in window.status._subject.text()
    window.close()
