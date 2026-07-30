"""Main window - explorer | hero viewport | timeline | inspector."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from motion_engine.studio.commands import CommandRegistry, register_builtin_commands
from motion_engine.studio.components.toast import show_toast
from motion_engine.studio.dialogs.about_dialog import AboutDialog
from motion_engine.studio.dialogs.open_project_dialog import OpenProjectDialog
from motion_engine.studio.dialogs.settings_dialog import SettingsDialog
from motion_engine.studio.docking import WorkspaceManager
from motion_engine.studio.events import ApplicationEventBus
from motion_engine.studio.icons import icon_app
from motion_engine.studio.models.playback_model import PlaybackModel, PlaybackState
from motion_engine.studio.models.session_model import SessionModel
from motion_engine.studio.models.subject_model import SubjectModel
from motion_engine.studio.panels.charts_panel import ChartsPanel
from motion_engine.studio.panels.inspector_panel import InspectorPanel
from motion_engine.studio.plugins.loader import load_plugins
from motion_engine.studio.services.export_service import ExportService, ExportServiceError
from motion_engine.studio.settings import StudioSettings
from motion_engine.studio.state import ApplicationState
from motion_engine.studio.theme import DEFAULT_THEME, apply_elevation, build_stylesheet, get_theme
from motion_engine.studio.undo import StudioUndoStack
from motion_engine.studio.viewport import ViewportSceneBridge
from motion_engine.studio.widgets.command_bar import CommandBar
from motion_engine.studio.widgets.command_palette import CommandPalette
from motion_engine.studio.widgets.error_banner import ErrorBanner
from motion_engine.studio.widgets.loading_overlay import LoadingOverlay
from motion_engine.studio.widgets.sidebar import Sidebar
from motion_engine.studio.widgets.status_bar import StatusSnapshot, StudioStatusBar
from motion_engine.studio.widgets.timeline_dock import TimelineDock
from motion_engine.studio.widgets.viewer_canvas import ViewerCanvas
from motion_engine.studio.widgets.welcome_screen import WelcomeScreen


class MainWindow(QMainWindow):
    """Shell: command bar | explorer dock | viewport | inspector | timeline."""

    def __init__(self, settings: StudioSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("AXYX")
        self.setWindowIcon(icon_app(64))
        self.resize(settings.window_width, settings.window_height)
        sp = DEFAULT_THEME.spacing

        self.commands = CommandRegistry(self)
        self.state = ApplicationState(self)
        self.events = ApplicationEventBus(self)
        self.undo_stack = StudioUndoStack()
        self.scene_bridge = ViewportSceneBridge()
        self._export_service = ExportService()
        self._layout_restored = False

        self.command_bar = CommandBar(self.commands)
        self.sidebar = Sidebar()
        self.session_browser = self.sidebar.session_browser
        self.viewer_canvas = ViewerCanvas()
        self.timeline_dock = TimelineDock()
        self.playback_toolbar = self.timeline_dock
        self.timeline = self.timeline_dock
        self.inspector = InspectorPanel()
        self.charts = ChartsPanel()
        self.welcome = WelcomeScreen()
        self.status = StudioStatusBar()
        self.setStatusBar(self.status)
        self._error_banner = ErrorBanner()
        self._sidebar_expanded = True

        apply_elevation(self.timeline_dock, level=1)

        stage = QWidget()
        stage_layout = QVBoxLayout(stage)
        stage_layout.setContentsMargins(sp.sm, sp.sm, sp.sm, sp.sm)
        stage_layout.setSpacing(sp.sm)
        stage_layout.addWidget(self._error_banner)
        stage_layout.addWidget(self.viewer_canvas, stretch=1)
        stage_layout.addWidget(self.timeline_dock)
        stage.setMinimumWidth(480)

        shell = QWidget()
        shell.setObjectName("Workspace")
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        shell_layout.addWidget(self.command_bar)
        shell_layout.addWidget(stage, stretch=1)

        self._stack = QStackedWidget()
        self._stack.addWidget(self.welcome)
        self._stack.addWidget(shell)
        self.setCentralWidget(self._stack)
        self._workspace = shell

        self._explorer_dock = QDockWidget("Explorer", self)
        self._explorer_dock.setObjectName("ExplorerDock")
        self._explorer_dock.setAccessibleName("Explorer")
        self._explorer_dock.setWidget(self.sidebar)
        apply_elevation(self.sidebar, level=1)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._explorer_dock)

        self._inspector_dock = QDockWidget("Inspector", self)
        self._inspector_dock.setObjectName("InspectorDock")
        self._inspector_dock.setAccessibleName("Inspector")
        self._inspector_dock.setWidget(self.inspector)
        apply_elevation(self.inspector, level=1)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._inspector_dock)

        self._charts_dock = QDockWidget("Charts", self)
        self._charts_dock.setObjectName("ChartsDock")
        self._charts_dock.setAccessibleName("Charts")
        self._charts_dock.setWidget(self.charts)
        apply_elevation(self.charts, level=1)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._charts_dock)
        self.tabifyDockWidget(self._inspector_dock, self._charts_dock)
        self._inspector_dock.raise_()

        self._workspace_manager = WorkspaceManager(self)
        self._workspace_manager.register_dock("explorer", self._explorer_dock)
        self._workspace_manager.register_dock("inspector", self._inspector_dock)
        self._workspace_manager.register_dock("charts", self._charts_dock)
        self._workspace_manager.set_default_recipe(self._apply_default_dock_layout)

        self._overlay = LoadingOverlay(self)
        self.controller = None
        self.scene_bridge.attach_viewer(self.viewer_canvas)

        self.command_bar.sidebarToggleRequested.connect(self.toggle_sidebar)
        self._connect_state_observers()
        self._connect_event_observers()
        load_plugins(
            main_window=self,
            commands=self.commands,
            workspace_manager=self._workspace_manager,
        )

    def _connect_state_observers(self) -> None:
        self.state.playbackChanged.connect(self._on_playback_state_changed)
        self.state.projectChanged.connect(self._on_project_state_changed)
        self.state.viewChanged.connect(self._on_view_state_changed)
        self.state.workspaceChanged.connect(self._on_workspace_state_changed)
        self.state.viewportChanged.connect(self._on_viewport_state_changed)
        self.state.selectionChanged.connect(self._on_selection_state_changed)
        self.state.inspectorChanged.connect(self._on_inspector_state_changed)

        stack = self.undo_stack.qt_stack
        stack.canUndoChanged.connect(self._update_undo_actions)
        stack.canRedoChanged.connect(self._update_undo_actions)

    def _connect_event_observers(self) -> None:
        self.events.sessionLoaded.connect(self._on_session_loaded)
        self.events.errorRaised.connect(self._on_error_raised)
        self.events.datasetLoaded.connect(self._on_dataset_loaded)
        self.events.frameChanged.connect(self._on_frame_changed)
        self.events.playbackChanged.connect(self._on_playback_event)

    def _on_playback_state_changed(self) -> None:
        snap = self.state.playback
        self.status._state.setText(
            snap.playback_state.value.upper()
            if hasattr(snap.playback_state, "value")
            else str(snap.playback_state).upper()
        )
        state_name = (
            snap.playback_state.value
            if hasattr(snap.playback_state, "value")
            else str(snap.playback_state)
        )
        self.status._state.setProperty("state", state_name)
        self.status._state.style().unpolish(self.status._state)
        self.status._state.style().polish(self.status._state)
        if snap.frame_count:
            self.status._frames.setText(f"Frames: {snap.frame}/{snap.frame_count}")

    def _on_project_state_changed(self) -> None:
        subject = self.state.project.subject_id or "—"
        session = self.state.project.session_name or "—"
        if subject != "—" or session != "—":
            self.setWindowTitle(f"AXYX — {subject}/{session}")
        else:
            self.setWindowTitle("AXYX")

    def _on_view_state_changed(self) -> None:
        expanded = self.state.view.sidebar_expanded
        if self._explorer_dock.isVisible() != expanded:
            self._explorer_dock.setVisible(expanded)
            self._sidebar_expanded = expanded

    def _on_workspace_state_changed(self) -> None:
        ws = self.state.workspace
        if self._explorer_dock.isVisible() != ws.explorer_visible:
            self._explorer_dock.setVisible(ws.explorer_visible)
        if self._inspector_dock.isVisible() != ws.inspector_visible:
            self._inspector_dock.setVisible(ws.inspector_visible)
        if self._charts_dock.isVisible() != ws.charts_visible:
            self._charts_dock.setVisible(ws.charts_visible)

    def _on_viewport_state_changed(self) -> None:
        enabled = self.state.viewport.avatar_enabled
        self.scene_bridge.set_layer_visible("avatar", enabled)
        summary = self.scene_bridge.summary()
        if summary.get("session"):
            self.inspector.set_scene(summary)
        preset = self.state.viewport.camera_preset
        if preset:
            self.status.showMessage(f"Camera: {preset}", 2000)

    def _on_selection_state_changed(self) -> None:
        sel = self.state.selection
        subject = sel.subject_id or "—"
        session = sel.session_name or "—"
        self.status._subject.setText(f"Subject: {subject}")
        self.status._session.setText(f"Session: {session}")

    def _on_inspector_state_changed(self) -> None:
        snap = self.state.inspector
        if snap.last_tab:
            self.status.showMessage(f"Inspector: {snap.last_tab}", 1500)

    def _on_session_loaded(self, subject_id: str, session_name: str) -> None:
        self.status.showMessage(f"Loaded session {subject_id}/{session_name}", 5000)
        avatar = self.state.viewport.avatar_enabled
        self.scene_bridge.set_session(subject_id, session_name, avatar_enabled=avatar)
        self.scene_bridge.sync()
        summary = self.scene_bridge.summary()
        self.inspector.set_scene(summary)
        self.state.set_inspector(last_tab="scene", dirty=False)

    def _on_error_raised(self, title: str, message: str) -> None:
        show_toast(self, f"{title}: {message}")

    def _on_dataset_loaded(self, path: str) -> None:
        name = Path(path).name if path else path
        self.status.showMessage(f"Dataset loaded: {name}", 5000)

    def _on_frame_changed(self, frame: int) -> None:
        charts = getattr(self, "charts", None)
        if charts is not None and hasattr(charts, "set_playhead"):
            charts.set_playhead(frame)
        snap = self.state.playback
        if snap.frame_count:
            self.status._frames.setText(f"Frames: {frame}/{snap.frame_count}")

    def _on_playback_event(self, state: str) -> None:
        self.status._state.setText(str(state).upper())
        self.status._state.setProperty("state", str(state).lower())
        self.status._state.style().unpolish(self.status._state)
        self.status._state.style().polish(self.status._state)

    def _update_undo_actions(self, *_args) -> None:
        if "edit.undo" in self.commands.all_ids():
            self.commands.set_enabled("edit.undo", self.undo_stack.can_undo())
        if "edit.redo" in self.commands.all_ids():
            self.commands.set_enabled("edit.redo", self.undo_stack.can_redo())

    def _setup_menus(self) -> None:
        bar = self.menuBar()
        bar.clear()
        bar.show()
        file_menu = bar.addMenu("&File")
        file_menu.addAction(self.commands.action("file.open"))
        if "file.export_json" in self.commands.all_ids():
            file_menu.addAction(self.commands.action("file.export_json"))

        edit_menu = bar.addMenu("&Edit")
        edit_menu.addAction(self.commands.action("edit.settings"))
        if "edit.undo" in self.commands.all_ids():
            edit_menu.addAction(self.commands.action("edit.undo"))
        if "edit.redo" in self.commands.all_ids():
            edit_menu.addAction(self.commands.action("edit.redo"))

        view_menu = bar.addMenu("&View")
        view_menu.addAction(self.commands.action("view.toggle_sidebar"))
        if "view.command_palette" in self.commands.all_ids():
            view_menu.addAction(self.commands.action("view.command_palette"))
        view_menu.addSeparator()
        if "view.workspace_research" in self.commands.all_ids():
            view_menu.addAction(self.commands.action("view.workspace_research"))
        if "view.workspace_focus" in self.commands.all_ids():
            view_menu.addAction(self.commands.action("view.workspace_focus"))
        if "view.workspace_review" in self.commands.all_ids():
            view_menu.addAction(self.commands.action("view.workspace_review"))
        if "view.workspace_reset" in self.commands.all_ids():
            view_menu.addAction(self.commands.action("view.workspace_reset"))
        view_menu.addSeparator()
        view_menu.addAction(self.commands.action("view.reset_camera"))
        if "view.toggle_avatar" in self.commands.all_ids():
            view_menu.addAction(self.commands.action("view.toggle_avatar"))
        if "view.toggle_charts" in self.commands.all_ids():
            view_menu.addAction(self.commands.action("view.toggle_charts"))
        if "view.fullscreen" in self.commands.all_ids():
            view_menu.addAction(self.commands.action("view.fullscreen"))
        view_menu.addSeparator()
        for cam_id in (
            "view.camera_front",
            "view.camera_back",
            "view.camera_left",
            "view.camera_right",
        ):
            if cam_id in self.commands.all_ids():
                view_menu.addAction(self.commands.action(cam_id))

        playback_menu = bar.addMenu("&Playback")
        playback_menu.addAction(self.commands.action("playback.play_pause"))
        playback_menu.addAction(self.commands.action("playback.stop"))

        help_menu = bar.addMenu("&Help")
        help_menu.addAction(self.commands.action("help.about"))
        if "plugin.hello" in self.commands.all_ids():
            help_menu.addAction(self.commands.action("plugin.hello"))

    def toggle_sidebar(self) -> None:
        """Show or hide the explorer dock."""
        visible = not self._explorer_dock.isVisible()
        self._explorer_dock.setVisible(visible)
        self._sidebar_expanded = visible
        self.state.set_view(sidebar_expanded=visible)

    def _open_command_palette(self) -> None:
        CommandPalette.open_palette(self, self.commands)

    def _apply_default_dock_layout(self) -> None:
        """Factory dock recipe used by Reset Workspace."""
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._explorer_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._inspector_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._charts_dock)
        self.tabifyDockWidget(self._inspector_dock, self._charts_dock)
        self._explorer_dock.show()
        self._inspector_dock.show()
        self._charts_dock.show()
        self._inspector_dock.raise_()

    def _apply_workspace_preset(
        self,
        name: str,
        *,
        explorer: bool,
        inspector: bool,
        charts: bool,
    ) -> None:
        self._workspace_manager.load_preset(name)
        self._explorer_dock.setVisible(explorer)
        self._inspector_dock.setVisible(inspector)
        self._charts_dock.setVisible(charts)
        self.state.set_workspace(
            preset_name=name,
            explorer_visible=explorer,
            inspector_visible=inspector,
            charts_visible=charts,
        )
        self._workspace_manager.save_preset(name)
        self._workspace_manager.save_layout()

    def _workspace_research(self) -> None:
        self._apply_workspace_preset("research", explorer=True, inspector=True, charts=True)

    def _workspace_focus(self) -> None:
        self._apply_workspace_preset("focus", explorer=True, inspector=False, charts=False)

    def _workspace_review(self) -> None:
        self._apply_workspace_preset("review", explorer=True, inspector=True, charts=True)

    def _workspace_reset(self) -> None:
        self._workspace_manager.reset_layout()
        self.state.set_workspace(
            preset_name=None,
            explorer_visible=True,
            inspector_visible=True,
            charts_visible=True,
        )

    def _toggle_charts(self) -> None:
        visible = not self._charts_dock.isVisible()
        self._charts_dock.setVisible(visible)
        self.state.set_workspace(charts_visible=visible)

    def show_welcome(self, visible: bool) -> None:
        self._stack.setCurrentIndex(0 if visible else 1)
        if not visible:
            self._explorer_dock.show()

    def attach_controller(self, controller: Any) -> None:
        self.controller = controller
        controller.state = self.state
        controller.events = self.events
        controller.undo_stack = self.undo_stack
        self.welcome.openDatasetRequested.connect(controller.open_default_dataset)
        self.sidebar.subjectSelected.connect(controller.select_subject)
        self.sidebar.recentSessionSelected.connect(controller.select_recent)
        self.sidebar.sessionSelected.connect(controller.select_session)
        dock = self.timeline_dock
        dock.playClicked.connect(controller.play)
        dock.pauseClicked.connect(controller.pause)
        dock.stopClicked.connect(controller.stop)
        dock.playPauseToggled.connect(self._on_play_pause_toggle)
        dock.previousClicked.connect(controller.previous_frame)
        dock.nextClicked.connect(controller.next_frame)
        dock.speedChanged.connect(controller.set_speed)
        dock.loopChanged.connect(controller.set_loop)
        dock.frameSeeked.connect(controller.seek)
        dock.resetCameraClicked.connect(self.viewer_canvas.reset_camera)
        self._setup_commands(controller)
        self._update_undo_actions()

    def _setup_commands(self, controller: Any) -> None:
        register_builtin_commands(
            self.commands,
            open_dataset=self._open_dataset_dialog,
            play_pause=self._toggle_play_pause,
            stop=controller.stop,
            reset_camera=self.viewer_canvas.reset_camera,
            toggle_sidebar=self.toggle_sidebar,
            open_settings=self._open_settings,
            open_about=self._open_about,
            export_animation=self._export_animation,
            undo=self.undo_stack.undo,
            redo=self.undo_stack.redo,
            open_command_palette=self._open_command_palette,
            workspace_research=self._workspace_research,
            workspace_focus=self._workspace_focus,
            workspace_reset=self._workspace_reset,
            workspace_review=self._workspace_review,
            toggle_avatar=self._toggle_avatar,
            camera_front=lambda: self._set_camera_preset("front"),
            camera_back=lambda: self._set_camera_preset("back"),
            camera_left=lambda: self._set_camera_preset("left"),
            camera_right=lambda: self._set_camera_preset("right"),
            toggle_fullscreen=self._toggle_fullscreen,
            toggle_charts=self._toggle_charts,
        )
        self.command_bar.bind_commands(self.commands)
        self._setup_menus()

    def _set_camera_preset(self, preset: str) -> None:
        self.viewer_canvas.set_camera_preset(preset)
        self.state.set_viewport(camera_preset=preset)

    def _toggle_fullscreen(self) -> None:
        canvas = self.viewer_canvas
        handler = getattr(canvas, "_on_fullscreen", None)
        if callable(handler):
            handler()

    def _toggle_avatar(self) -> None:
        canvas = self.viewer_canvas
        enabled = not bool(getattr(canvas, "_digital_twin_enabled", False))
        canvas.set_digital_twin_enabled(enabled)
        self.scene_bridge.set_layer_visible("avatar", enabled)
        self.state.set_viewport(avatar_enabled=enabled)
        self.state.set_view(avatar_enabled=enabled)
        self.inspector.set_scene(self.scene_bridge.summary())

    def _toggle_play_pause(self) -> None:
        if self.controller is None:
            return
        model = self.controller.playback.model
        if model.state == PlaybackState.PLAYING:
            self.controller.pause()
        else:
            self.controller.play()

    def _on_play_pause_toggle(self) -> None:
        self._toggle_play_pause()

    def _export_animation(self) -> None:
        if self.controller is None:
            return
        clip = self.controller.motion.clip
        if clip is None:
            self.show_error("Export", "Load a session before exporting animation JSON.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Animation JSON",
            "",
            "JSON (*.json)",
        )
        if not path:
            return
        try:
            out = self._export_service.export_animation_json(clip, Path(path))
            self.status.showMessage(f"Exported {out.name}", 5000)
        except ExportServiceError as exc:
            self.show_error("Export Error", str(exc))

    def show_loading(self, message: str | None) -> None:
        if message:
            self._overlay.show_message(message)
        else:
            self._overlay.hide_overlay()

    def show_loading_progress(self, value: int) -> None:
        if value <= 0:
            return
        self._overlay.set_progress(value)

    def set_subjects(self, subjects: list[SubjectModel]) -> None:
        self.sidebar.set_subjects(subjects)

    def set_sessions(self, subject_id: str, sessions: list[SessionModel]) -> None:
        self.sidebar.set_sessions(subject_id, sessions)

    def clear_sessions(self) -> None:
        self.sidebar.clear_sessions()

    def set_recent_sessions(self, keys: list[str]) -> None:
        self.sidebar.set_recent_sessions(keys)

    def set_skeleton_preview(self, skeleton, frame: int) -> None:
        self.viewer_canvas.set_skeleton(skeleton, frame)

    def sync_playback(self, model: PlaybackModel) -> None:
        self.timeline_dock.sync_from_model(model)

    def set_inspector_clinical(self, fields: dict) -> None:
        self.inspector.set_clinical(fields)

    def set_inspector_metrics(self, metrics: dict) -> None:
        self.inspector.set_metrics(metrics)
        charts = getattr(self, "charts", None)
        if charts is not None:
            charts.set_metrics(metrics)

    def set_inspector_dataset(self, fields: dict) -> None:
        self.inspector.set_dataset(fields)

    def set_inspector_playback(self, fields: dict) -> None:
        self.inspector.set_playback(fields)

    def update_status(self, snapshot: StatusSnapshot) -> None:
        self.status.update_snapshot(snapshot)

    def show_error(self, title: str, message: str) -> None:
        if self._stack.currentIndex() == 0 and title.lower().startswith("dataset"):
            QMessageBox.critical(self, title, message)
            return
        self._error_banner.show_error(title, message)
        self.status.showMessage(f"{title}: {message}", 8000)
        self.events.emit_error(title, message)

    def _open_dataset_dialog(self) -> None:
        dialog = OpenProjectDialog(self.settings.dataset_path, self)
        if dialog.exec():
            path = dialog.selected_path()
            if self.controller is not None:
                self.controller.open_dataset(str(path) if path else None)

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            app = QApplication.instance()
            if app is not None:
                app.setStyleSheet(build_stylesheet(get_theme(self.settings.theme_mode)))

    def _open_about(self) -> None:
        AboutDialog(self).exec()

    def showEvent(self, event) -> None:  # noqa: N802
        if not self._layout_restored:
            self._workspace_manager.restore_layout()
            self._layout_restored = True
        super().showEvent(event)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._workspace_manager.save_layout()
        self.settings.window_width = self.width()
        self.settings.window_height = self.height()
        self.settings.save()
        if self.controller is not None:
            self.controller.shutdown()
        super().closeEvent(event)

    def resizeEvent(self, event) -> None:  # noqa: N802
        self._overlay.setGeometry(self.rect())
        super().resizeEvent(event)
