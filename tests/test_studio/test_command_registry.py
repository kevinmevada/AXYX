"""Tests for CommandRegistry."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from motion_engine.studio.commands import Command, CommandRegistry


def test_register_execute_and_action() -> None:
    QApplication.instance() or QApplication([])
    registry = CommandRegistry()
    seen: list[str] = []

    registry.register(
        Command(id="test.run", text="Run", shortcut="Ctrl+R"),
        lambda: seen.append("ok"),
    )
    registry.execute("test.run")
    assert seen == ["ok"]

    action = registry.action("test.run")
    assert action.text() == "Run"
    assert action.shortcut().toString() == "Ctrl+R"

    registry.set_enabled("test.run", False)
    assert registry.action("test.run").isEnabled() is False
    assert registry.all_ids() == ["test.run"]
