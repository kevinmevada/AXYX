"""Sample console plugin — demonstrates the plugin entry-point API."""
from __future__ import annotations
from PySide6.QtWidgets import QMessageBox
from motion_engine.studio.commands.command import Command
from motion_engine.studio.plugins.api import PluginContext

class SampleConsolePlugin:
    """Registers a hello command that shows a status message."""
    def activate(self, ctx: PluginContext) -> None:
        window = ctx.main_window
        def hello() -> None:
            if hasattr(window, "status"):
                window.status.showMessage("Hello from sample_console plugin", 4000)
            QMessageBox.information(window, "Sample Plugin", "Hello from AXYX sample plugin!")
        ctx.register_command(
            Command(
                id="plugin.hello",
                text="Sample Plugin: Hello",
                tooltip="Demonstrate the studio plugin API",
            ),
            hello,
        )
