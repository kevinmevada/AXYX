"""Persist and restore QMainWindow dock layouts via QSettings."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PySide6.QtCore import QByteArray, QSettings, Qt
from PySide6.QtWidgets import QDockWidget, QMainWindow


class WorkspaceManager:
    """Register named docks and save/restore the main-window layout."""

    _PRESETS_DIR = Path.home() / ".axyx" / "workspace" / "presets"
    _PRESET_VERSION = 1

    def __init__(
        self,
        main_window: QMainWindow,
        settings_key: str = "workspace/layout",
    ) -> None:
        self._window = main_window
        self._settings_key = settings_key
        self._docks: dict[str, QDockWidget] = {}
        self._default_recipe: Callable[[], None] | None = None
        self._PRESETS_DIR.mkdir(parents=True, exist_ok=True)

    def register_dock(self, name: str, dock: QDockWidget) -> None:
        """Track a dock widget under a stable settings key."""
        self._docks[name] = dock

    def set_default_recipe(self, recipe: Callable[[], None]) -> None:
        """Install the callable that rebuilds the factory dock layout."""
        self._default_recipe = recipe

    def dock(self, name: str) -> QDockWidget | None:
        return self._docks.get(name)

    def visibility(self) -> dict[str, bool]:
        return {key: dock.isVisible() for key, dock in self._docks.items()}

    def apply_visibility(self, visibility: dict[str, bool]) -> None:
        for key, visible in visibility.items():
            dock = self._docks.get(key)
            if dock is not None:
                dock.setVisible(bool(visible))

    def _preset_path(self, name: str) -> Path:
        safe = name.replace("/", "_").replace("\\", "_").strip()
        return self._PRESETS_DIR / f"{safe}.json"

    def save_layout(self) -> None:
        """Persist the current main-window geometry and dock state."""
        settings = QSettings()
        settings.setValue(self._settings_key, self._window.saveState())
        settings.setValue(f"{self._settings_key}/geometry", self._window.saveGeometry())

    def restore_layout(self) -> bool:
        """Restore a previously saved layout. Returns True on success."""
        settings = QSettings()
        state: Any = settings.value(self._settings_key)
        geometry: Any = settings.value(f"{self._settings_key}/geometry")
        restored = False
        if geometry is not None:
            self._window.restoreGeometry(geometry)
            restored = True
        if state is not None:
            self._window.restoreState(state)
            restored = True
        return restored

    def clear_saved_layout(self) -> None:
        """Remove persisted layout keys so the next restore starts fresh."""
        settings = QSettings()
        settings.remove(self._settings_key)
        settings.remove(f"{self._settings_key}/geometry")

    def save_preset(self, name: str) -> None:
        """Save current dock layout and visibility under ``name``."""
        visibility = self.visibility()
        payload = {
            "version": self._PRESET_VERSION,
            "state": bytes(self._window.saveState().toHex()).decode("ascii"),
            "geometry": bytes(self._window.saveGeometry().toHex()).decode("ascii"),
            "visibility": visibility,
        }
        path = self._preset_path(name)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load_preset(self, name: str) -> bool:
        """Restore a named preset. Returns True on success."""
        path = self._preset_path(name)
        if not path.is_file():
            return False
        payload = json.loads(path.read_text(encoding="utf-8"))
        geometry_hex = payload.get("geometry")
        state_hex = payload.get("state")
        if geometry_hex:
            self._window.restoreGeometry(QByteArray.fromHex(geometry_hex.encode("ascii")))
        if state_hex:
            self._window.restoreState(QByteArray.fromHex(state_hex.encode("ascii")))
        visibility = payload.get("visibility", {})
        self.apply_visibility(visibility)
        return True

    def list_presets(self) -> list[str]:
        """Return saved preset names."""
        return sorted(p.stem for p in self._PRESETS_DIR.glob("*.json"))

    def reset_layout(self) -> None:
        """Rebuild the factory dock layout and persist it."""
        self.clear_saved_layout()
        if self._default_recipe is not None:
            self._default_recipe()
        else:
            for dock in self._docks.values():
                dock.show()
                self._window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
        self.save_layout()
