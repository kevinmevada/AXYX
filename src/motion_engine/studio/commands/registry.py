"""Central command registry — QAction factory and execution."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QKeySequence

from motion_engine.studio.commands.command import Command


class CommandRegistry(QObject):
    """Register commands, expose QAction instances, and execute by id."""

    commandExecuted = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._commands: dict[str, Command] = {}
        self._handlers: dict[str, Callable[[], None]] = {}
        self._actions: dict[str, QAction] = {}

    def register(self, command: Command, handler: Callable[[], None]) -> None:
        """Bind ``command`` to ``handler`` and cache metadata."""
        self._commands[command.id] = command
        self._handlers[command.id] = handler
        if command.id in self._actions:
            action = self._actions[command.id]
            action.setText(command.text)
            action.setToolTip(command.tooltip or command.text)
            if command.shortcut:
                action.setShortcut(QKeySequence(command.shortcut))
            action.setEnabled(command.enabled)
            action.setCheckable(command.checkable)
            if command.checkable:
                action.setChecked(command.checked)

    def action(self, command_id: str) -> QAction:
        """Return a cached QAction wired to ``command_id``."""
        if command_id not in self._commands:
            raise KeyError(f"Unknown command: {command_id}")
        if command_id not in self._actions:
            cmd = self._commands[command_id]
            action = QAction(cmd.text, self)
            action.setObjectName(f"Command_{command_id.replace('.', '_')}")
            if cmd.tooltip:
                action.setToolTip(cmd.tooltip)
            if cmd.shortcut:
                action.setShortcut(QKeySequence(cmd.shortcut))
            action.setEnabled(cmd.enabled)
            action.setCheckable(cmd.checkable)
            if cmd.checkable:
                action.setChecked(cmd.checked)
            action.triggered.connect(lambda _checked=False, cid=command_id: self.execute(cid))
            self._actions[command_id] = action
        return self._actions[command_id]

    def execute(self, command_id: str) -> None:
        """Run the handler for ``command_id``."""
        handler = self._handlers.get(command_id)
        if handler is None:
            raise KeyError(f"No handler registered for command: {command_id}")
        handler()
        self.commandExecuted.emit(command_id)

    def set_enabled(self, command_id: str, enabled: bool) -> None:
        """Toggle command and QAction enabled state."""
        cmd = self._commands.get(command_id)
        if cmd is None:
            raise KeyError(f"Unknown command: {command_id}")
        self._commands[command_id] = Command(
            id=cmd.id,
            text=cmd.text,
            shortcut=cmd.shortcut,
            tooltip=cmd.tooltip,
            enabled=enabled,
            checkable=cmd.checkable,
            checked=cmd.checked,
            execute=cmd.execute,
        )
        if command_id in self._actions:
            self._actions[command_id].setEnabled(enabled)

    def all_ids(self) -> list[str]:
        """Return registered command ids in insertion order."""
        return list(self._commands.keys())

    def get(self, command_id: str) -> Command:
        """Return command metadata for ``command_id``."""
        cmd = self._commands.get(command_id)
        if cmd is None:
            raise KeyError(f"Unknown command: {command_id}")
        return cmd
