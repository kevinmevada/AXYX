"""Tests for CommandPalette."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from motion_engine.studio.commands import Command, CommandRegistry
from motion_engine.studio.widgets.command_palette import CommandPalette


def test_command_palette_filter_and_execute() -> None:
    QApplication.instance() or QApplication([])
    registry = CommandRegistry()
    executed: list[str] = []

    registry.register(
        Command(id="file.open", text="Open Dataset"),
        lambda: executed.append("open"),
    )
    registry.register(
        Command(id="view.reset_camera", text="Reset Camera"),
        lambda: executed.append("camera"),
    )

    palette = CommandPalette(registry)
    palette._filter.setText("reset")
    assert palette._list.count() == 1
    assert "Reset Camera" in palette._list.item(0).text()

    palette._filter.setText("")
    assert palette._list.count() >= 2

    palette._list.setCurrentRow(0)
    command_id = palette._list.currentItem().data(Qt.ItemDataRole.UserRole)
    registry.execute(str(command_id))
    assert executed

    palette.close()
