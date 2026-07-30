"""Load studio plugins from entry points."""

from __future__ import annotations

import importlib.metadata
import logging
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMainWindow

from motion_engine.studio.commands.registry import CommandRegistry
from motion_engine.studio.plugins.api import PluginContext

if TYPE_CHECKING:
    from motion_engine.studio.docking.workspace_manager import WorkspaceManager

logger = logging.getLogger(__name__)

_ENTRY_GROUP = "axyx.studio_plugins"
_sample_loaded = False


def load_plugins(
    *,
    main_window: QMainWindow,
    commands: CommandRegistry,
    workspace_manager: WorkspaceManager | None = None,
) -> list[str]:
    """Load plugins from ``axyx.studio_plugins``; return activated names."""
    global _sample_loaded
    activated: list[str] = []
    ctx = PluginContext(
        main_window=main_window,
        commands=commands,
        workspace_manager=workspace_manager,
    )
    try:
        entries = importlib.metadata.entry_points(group=_ENTRY_GROUP)
    except TypeError:  # Python <3.10 compat
        entries = importlib.metadata.entry_points().get(_ENTRY_GROUP, ())  # type: ignore[union-attr]

    for entry in entries:
        try:
            plugin_factory = entry.load()
            plugin = plugin_factory() if callable(plugin_factory) else plugin_factory
            activate = getattr(plugin, "activate", None)
            if callable(activate):
                activate(ctx)
                activated.append(entry.name)
        except Exception:  # noqa: BLE001 — plugins are optional
            logger.exception("Failed to load studio plugin %s", entry.name)

    if not _sample_loaded and "sample_console" not in activated:
        try:
            from motion_engine.studio.plugins.sample_console_plugin import SampleConsolePlugin

            SampleConsolePlugin().activate(ctx)
            activated.append("sample_console")
        except Exception:  # noqa: BLE001
            logger.exception("Failed to load built-in sample_console plugin")
    _sample_loaded = True

    return activated
