"""Workspace manager, scene bridge, and settings validation."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDockWidget, QLabel, QMainWindow

from motion_engine.studio.docking.workspace_manager import WorkspaceManager
from motion_engine.studio.settings import StudioSettings
from motion_engine.studio.viewport.scene_bridge import ViewportSceneBridge


def test_scene_bridge_builds_render_layers() -> None:
    bridge = ViewportSceneBridge()
    bridge.set_session("S2", "WU01", avatar_enabled=True)
    names = {n.name for n in bridge.scene_graph.root.walk() if n.name != "studio_viewport"}
    assert "S2/WU01" in names
    assert {"skeleton", "avatar", "ground"} <= names
    summary = bridge.summary()
    assert summary["session"] == "S2/WU01"
    assert summary["render_node_count"] == 3
    assert bridge.set_layer_visible("avatar", False)
    assert bridge.scene_graph.find("avatar").visible is False


def test_settings_validate_clamps() -> None:
    settings = StudioSettings(
        organization="AXYXTest",
        application="SettingsClamp",
        window_width=10,
        window_height=99999,
        playback_speed=99.0,
        theme_mode="neon",
        recent_subjects=[f"S{i}" for i in range(40)],
    )
    settings.validate()
    assert settings.window_width == 800
    assert settings.window_height == 4320
    assert settings.playback_speed == 4.0
    assert settings.theme_mode == "light"
    assert len(settings.recent_subjects) == 12


def test_workspace_preset_roundtrip(tmp_path: Path, monkeypatch) -> None:
    QApplication.instance() or QApplication([])
    monkeypatch.setattr(WorkspaceManager, "_PRESETS_DIR", tmp_path / "presets")
    window = QMainWindow()
    window.show()
    left = QDockWidget("L", window)
    left.setWidget(QLabel("a"))
    window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, left)
    mgr = WorkspaceManager(window)
    mgr.register_dock("explorer", left)
    left.hide()
    mgr.save_preset("focus")
    left.show()
    assert mgr.load_preset("focus")
    assert left.isHidden()
    assert mgr.visibility()["explorer"] is False
    assert "focus" in mgr.list_presets()
