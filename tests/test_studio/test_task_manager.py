"""Tests for TaskManager."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtWidgets import QApplication

from motion_engine.studio.tasks import TaskManager


def _wait_until(predicate, *, timeout_ms: int = 3000) -> None:
    app = QCoreApplication.instance()
    assert app is not None
    if predicate():
        return
    loop = []
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.append)
    deadline = timeout_ms
    step = 50
    while deadline > 0 and not predicate():
        timer.start(step)
        while not loop and timer.isActive():
            app.processEvents()
        loop.clear()
        deadline -= step
    assert predicate()


def test_task_manager_success() -> None:
    QApplication.instance() or QApplication([])
    manager = TaskManager()
    results: list[int] = []

    manager.submit(
        lambda: 42,
        on_success=results.append,
        on_error=lambda exc: (_ for _ in ()).throw(exc),
    )
    _wait_until(lambda: results == [42])


def test_task_manager_error() -> None:
    QApplication.instance() or QApplication([])
    manager = TaskManager()
    errors: list[str] = []

    def _fail() -> None:
        raise ValueError("boom")

    manager.submit(
        _fail,
        on_success=lambda _: None,
        on_error=lambda exc: errors.append(str(exc)),
    )
    _wait_until(lambda: errors == ["boom"])
