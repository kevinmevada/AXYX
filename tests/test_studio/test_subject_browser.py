"""Tests for subject browser widget."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from motion_engine.studio.models.subject_model import SubjectModel
from motion_engine.studio.widgets.subject_browser import SubjectBrowser


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    return app


def test_subject_browser_lists_and_emits(qapp) -> None:
    browser = SubjectBrowser()
    subjects = [
        SubjectModel("S1", session_count=2),
        SubjectModel("S2", session_count=5, pinned=True),
        SubjectModel("S10", session_count=1),
    ]
    browser.set_subjects(subjects)
    assert browser._list.count() == 3

    selected: list[str] = []
    browser.subjectSelected.connect(selected.append)
    browser.select_subject("S2")
    assert selected == ["S2"]

    browser.set_cohort_filter({"S1", "S10"})
    assert browser._list.count() == 2
