"""Studio plugin API."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QMainWindow

from motion_engine.studio.commands.command import Command
from motion_engine.studio.commands.registry import CommandRegistry

if TYPE_CHECKING:
    from motion_engine.studio.docking.workspace_manager import WorkspaceManager


class PluginContext:
    """Surface exposed to third-party studio plugins."""

    def __init__(
        self,
        *,
        main_window: QMainWindow,
        commands: CommandRegistry,
        workspace_manager: WorkspaceManager | None = None,
    ) -> None:
        self.main_window = main_window
        self.commands = commands
        self.workspace_manager = workspace_manager
        self._docks: dict[str, QDockWidget] = {}

    def register_command(
        self,
        command: Command,
        handler: Callable[[], None],
    ) -> None:
        self.commands.register(command, handler)

    def register_dock(
        self,
        name: str,
        dock: QDockWidget,
        area: Qt.DockWidgetArea = Qt.DockWidgetArea.RightDockWidgetArea,
    ) -> None:
        self._docks[name] = dock
        self.main_window.addDockWidget(area, dock)
        if self.workspace_manager is not None:
            self.workspace_manager.register_dock(name, dock)


class Plugin(Protocol):
    """Entry-point plugin contract."""

    def activate(self, ctx: PluginContext) -> None: ...
