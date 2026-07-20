"""Tests for session browser widget."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from motion_engine.studio.models.session_model import SessionModel
from motion_engine.studio.widgets.session_browser import SessionBrowser


def test_session_browser_lists_and_emits() -> None:
    QApplication.instance() or QApplication([])
    browser = SessionBrowser()
    sessions = [
        SessionModel("S2", "WU01", classification="WarmUp", frame_count=100),
        SessionModel("S2", "NW01", classification="NormalWalk", frame_count=200),
    ]
    browser.set_sessions("S2", sessions)
    assert browser._list.count() == 2
    selected: list[str] = []
    browser.sessionSelected.connect(selected.append)
    browser._on_item_clicked(browser._list.item(0))
    assert selected[0] in {"WU01", "NW01"}
