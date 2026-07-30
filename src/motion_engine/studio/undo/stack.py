"""Undo/redo stack wrapper."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QUndoCommand, QUndoStack

class StudioUndoStack:
    """Thin wrapper around :class:`QUndoStack`."""

    def __init__(self) -> None:
        self._stack = QUndoStack()

    @property
    def qt_stack(self) -> QUndoStack:
        return self._stack

    def push(self, command: QUndoCommand) -> None:
        self._stack.push(command)

    def undo(self) -> None:
        self._stack.undo()

    def redo(self) -> None:
        self._stack.redo()

    def can_undo(self) -> bool:
        return self._stack.canUndo()

    def can_redo(self) -> bool:
        return self._stack.canRedo()

class SelectSessionCommand(QUndoCommand):
    """Undoable session selection."""

    def __init__(
        self,
        *,
        previous: str | None,
        new: str | None,
        apply_session: Callable[[str | None], None],
        text: str = "Select Session",
    ) -> None:
        super().__init__(text)
        self._previous = previous
        self._new = new
        self._apply = apply_session

    def undo(self) -> None:
        self._apply(self._previous)

    def redo(self) -> None:
        self._apply(self._new)

class SelectSubjectCommand(QUndoCommand):
    """Undoable subject selection."""

    def __init__(
        self,
        *,
        previous: str | None,
        new: str | None,
        apply_subject: Callable[[str | None], None],
        text: str = "Select Subject",
    ) -> None:
        super().__init__(text)
        self._previous = previous
        self._new = new
        self._apply = apply_subject

    def undo(self) -> None:
        self._apply(self._previous)

    def redo(self) -> None:
        self._apply(self._new)

