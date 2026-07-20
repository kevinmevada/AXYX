"""Tests for studio status bar."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from motion_engine.studio.widgets.status_bar import StatusSnapshot, StudioStatusBar


def test_status_bar_updates_labels() -> None:
    QApplication.instance() or QApplication([])
    bar = StudioStatusBar()
    bar.update_snapshot(
        StatusSnapshot(
            dataset="data.mat",
            subject="S2",
            session="WU01",
            frames=306,
            current_frame=12,
            fps=100.0,
            duration_sec=3.05,
            playback_state="playing",
            memory_mb=128.0,
            renderer="pyvista",
            cpu_percent=12.0,
        )
    )
    assert "S2" in bar._subject.text()
    assert "WU01" in bar._session.text()
    assert "306" in bar._frames.text()
    assert "playing" in bar._state.text().lower()
    assert "pyvista" in bar._renderer.text().lower()
    assert "12" in bar._cpu.text()
