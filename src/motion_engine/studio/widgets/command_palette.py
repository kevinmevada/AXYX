"""Command palette — filterable command launcher."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from motion_engine.studio.commands.registry import CommandRegistry

_CATEGORY_LABELS = {
    "file": "File",
    "edit": "Edit",
    "view": "View",
    "playback": "Playback",
    "help": "Help",
    "plugin": "Plugins",
}


def _category(command_id: str) -> str:
    prefix = command_id.split(".", 1)[0]
    return _CATEGORY_LABELS.get(prefix, prefix.title())


class CommandPalette(QDialog):
    """Frameless command picker with keyboard navigation."""

    def __init__(
        self,
        registry: CommandRegistry,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Command Palette")
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setModal(True)
        self.setMinimumSize(480, 360)
        self._registry = registry
        self._all_items: list[tuple[str, str, str]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        hint = QLabel("Type to filter commands")
        hint.setObjectName("MutedLabel")
        layout.addWidget(hint)

        self._filter = QLineEdit()
        self._filter.setPlaceholderText("Command palette…")
        self._filter.textChanged.connect(self._apply_filter)
        self._filter.installEventFilter(self)
        layout.addWidget(self._filter)

        self._list = QListWidget()
        self._list.itemActivated.connect(self._execute_current)
        self._list.installEventFilter(self)
        layout.addWidget(self._list, stretch=1)

        self._build_items()

    def _build_items(self) -> None:
        self._all_items.clear()
        for command_id in self._registry.all_ids():
            cmd = self._registry.get(command_id)
            category = _category(command_id)
            label = f"{category} › {cmd.text}"
            self._all_items.append((command_id, label, category))
        self._apply_filter("")

    def _apply_filter(self, text: str) -> None:
        needle = text.strip().lower()
        self._list.clear()
        for command_id, label, category in self._all_items:
            haystack = f"{category} {label} {command_id}".lower()
            if needle and needle not in haystack:
                continue
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, command_id)
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _execute_current(self, item: QListWidgetItem | None = None) -> None:
        current = item or self._list.currentItem()
        if current is None:
            return
        command_id = current.data(Qt.ItemDataRole.UserRole)
        if command_id:
            self._registry.execute(str(command_id))
            self.accept()

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if event.type() == event.Type.KeyPress:
            key = event.key()
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._execute_current()
                return True
            if key == Qt.Key.Key_Escape:
                self.reject()
                return True
            if key == Qt.Key.Key_Down and obj is self._filter:
                self._list.setFocus()
                if self._list.count():
                    self._list.setCurrentRow(0)
                return True
            if key == Qt.Key.Key_Up and obj is self._list and self._list.currentRow() <= 0:
                self._filter.setFocus()
                return True
        return super().eventFilter(obj, event)

    @staticmethod
    def open_palette(parent: QWidget | None, registry: CommandRegistry) -> None:
        """Show the palette modally."""
        dialog = CommandPalette(registry, parent)
        dialog._filter.setFocus()
        dialog.exec()
