"""Viewport host surface tests (offscreen-safe)."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("PySide6")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from motion_engine.studio.widgets.viewport import Viewport


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_viewport_alias(qapp) -> None:
    viewport = Viewport()
    assert hasattr(viewport, "show_skeleton")
    assert hasattr(viewport, "set_frame")
    assert hasattr(viewport, "reset_camera")
