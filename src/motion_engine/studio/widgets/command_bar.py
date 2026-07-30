"""Minimal top bar - brand, sidebar toggle, open dataset."""
from __future__ import annotations
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget
from motion_engine.studio.commands.registry import CommandRegistry
from motion_engine.studio.components.icon_button import IconButton
from motion_engine.studio.icons import icon_app
from motion_engine.studio.theme import DEFAULT_THEME

class CommandBar(QWidget):
    """Clean Apple-style top chrome with essential navigation."""
    sidebarToggleRequested = Signal()
    commandPaletteRequested = Signal()
    def __init__(
        self,
        commands: CommandRegistry | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("CommandBar")
        self.setAccessibleName("Command bar")
        self.setFixedHeight(44)
        self._commands = commands
        sp = DEFAULT_THEME.spacing
        icon_color = DEFAULT_THEME.colors.text_primary
        layout = QHBoxLayout(self)
        layout.setContentsMargins(sp.md, sp.xs, sp.md, sp.xs)
        layout.setSpacing(sp.sm)
        self._toggle = IconButton(
            "menu",
            tooltip="Toggle explorer (Ctrl+B)",
            size=28,
        )
        self._toggle.setAccessibleName("Toggle explorer")
        self._toggle.clicked.connect(self.sidebarToggleRequested.emit)
        layout.addWidget(self._toggle)
        mark = QLabel()
        mark.setPixmap(icon_app(24).pixmap(24, 24))
        title = QLabel("AXYX")
        title.setObjectName("BrandTitle")
        layout.addWidget(mark)
        layout.addWidget(title)
        layout.addStretch(1)
        self._palette_btn = IconButton(
            "search",
            tooltip="Command palette (Ctrl+Shift+P)",
            size=28,
        )
        self._palette_btn.setAccessibleName("Open command palette")
        self._palette_btn.clicked.connect(self.commandPaletteRequested.emit)
        layout.addWidget(self._palette_btn)
        self._open_btn = IconButton(
            "folder-open",
            tooltip="Open dataset (Ctrl+O)",
            size=28,
        )
        self._open_btn.setAccessibleName("Open dataset")
        layout.addWidget(self._open_btn)
    def bind_commands(self, registry: CommandRegistry) -> None:
        """Wire toolbar buttons to registry actions."""
        self._commands = registry
        self._toggle.setDefaultAction(registry.action("view.toggle_sidebar"))
        self._open_btn.setDefaultAction(registry.action("file.open"))
        if "view.command_palette" in registry.all_ids():
            self._palette_btn.setDefaultAction(registry.action("view.command_palette"))
