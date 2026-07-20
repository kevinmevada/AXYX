"""Main window - explorer | hero viewport | timeline only."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from motion_engine.studio.dialogs.about_dialog import AboutDialog
from motion_engine.studio.dialogs.open_project_dialog import OpenProjectDialog
from motion_engine.studio.dialogs.settings_dialog import SettingsDialog
from motion_engine.studio.icons import icon_app
from motion_engine.studio.models.playback_model import PlaybackModel
from motion_engine.studio.models.session_model import SessionModel
from motion_engine.studio.models.subject_model import SubjectModel
from motion_engine.studio.settings import StudioSettings
from motion_engine.studio.theme import DEFAULT_THEME, apply_elevation
from motion_engine.studio.widgets.command_bar import CommandBar
from motion_engine.studio.widgets.error_banner import ErrorBanner
from motion_engine.studio.widgets.loading_overlay import LoadingOverlay
from motion_engine.studio.widgets.sidebar import Sidebar
from motion_engine.studio.widgets.status_bar import StatusSnapshot, StudioStatusBar
from motion_engine.studio.widgets.timeline_dock import TimelineDock
from motion_engine.studio.widgets.viewer_canvas import ViewerCanvas
from motion_engine.studio.widgets.welcome_screen import WelcomeScreen


class MainWindow(QMainWindow):
    """Minimal shell: toolbar | browser | viewport | timeline | status.

    Implements :class:`~motion_engine.studio.controller.StudioView`.
    Inspector methods are no-ops (panel removed; status bar carries context).
    """

    def __init__(self, settings: StudioSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("AXYX")
        self.setWindowIcon(icon_app(64))
        self.resize(settings.window_width, settings.window_height)
        sp = DEFAULT_THEME.spacing

        self.command_bar = CommandBar()
        self.sidebar = Sidebar()
        self.session_browser = self.sidebar.session_browser
        self.viewer_canvas = ViewerCanvas()
        self.timeline_dock = TimelineDock()
        self.playback_toolbar = self.timeline_dock
        self.timeline = self.timeline_dock
        self.welcome = WelcomeScreen()
        self.status = StudioStatusBar()
        self.setStatusBar(self.status)
        self._error_banner = ErrorBanner()
        self._sidebar_expanded = True
        self._sidebar_width = 260

        apply_elevation(self.sidebar, level=1)
        apply_elevation(self.timeline_dock, level=1)

        stage = QWidget()
        stage_layout = QVBoxLayout(stage)
        stage_layout.setContentsMargins(0, 0, 0, 0)
        stage_layout.setSpacing(sp.sm)
        stage_layout.addWidget(self._error_banner)
        stage_layout.addWidget(self.viewer_canvas, stretch=1)
        stage_layout.addWidget(self.timeline_dock)
        stage.setMinimumWidth(480)

        self._workspace = QSplitter()
        self._workspace.setObjectName("Workspace")
        self._workspace.setContentsMargins(sp.sm, sp.sm, sp.sm, sp.sm)
        self._workspace.setHandleWidth(sp.sm)
        self._workspace.setChildrenCollapsible(False)
        self._workspace.addWidget(self.sidebar)
        self._workspace.addWidget(stage)
        self._workspace.setStretchFactor(0, 0)
        self._workspace.setStretchFactor(1, 1)
        self._workspace.setSizes([260, 1200])
        self.sidebar.setMinimumWidth(200)
        self.sidebar.setMaximumWidth(320)

        shell = QWidget()
        shell.setObjectName("Workspace")
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        shell_layout.addWidget(self.command_bar)
        shell_layout.addWidget(self._workspace, stretch=1)

        self._stack = QStackedWidget()
        self._stack.addWidget(self.welcome)
        self._stack.addWidget(shell)
        self.setCentralWidget(self._stack)

        self._overlay = LoadingOverlay(self)
        self.menuBar().hide()
        self.controller = None

        self.command_bar.sidebarToggleRequested.connect(self.toggle_sidebar)

    def toggle_sidebar(self) -> None:
        """Collapse/expand explorer - viewport absorbs freed space (no blank gap)."""
        total = max(self._workspace.width(), 800)
        if self._sidebar_expanded:
            self._sidebar_width = max(self.sidebar.width(), 200)
            self.sidebar.setMinimumWidth(0)
            self.sidebar.setMaximumWidth(0)
            self.sidebar.hide()
            self._workspace.setSizes([0, total])
            self._sidebar_expanded = False
        else:
            self.sidebar.setMinimumWidth(200)
            self.sidebar.setMaximumWidth(320)
            self.sidebar.show()
            w = min(max(self._sidebar_width, 200), total // 3)
            self._workspace.setSizes([w, max(total - w, 1)])
            self._sidebar_expanded = True

    def show_welcome(self, visible: bool) -> None:
        self._stack.setCurrentIndex(0 if visible else 1)
        if not visible and self._sidebar_expanded:
            self.sidebar.setMinimumWidth(200)
            self.sidebar.setMaximumWidth(320)
            self.sidebar.show()

    def attach_controller(self, controller: Any) -> None:
        self.controller = controller
        self.welcome.openDatasetRequested.connect(controller.open_default_dataset)
        self.sidebar.subjectSelected.connect(controller.select_subject)
        self.sidebar.recentSessionSelected.connect(controller.select_recent)
        self.sidebar.sessionSelected.connect(controller.select_session)
        dock = self.timeline_dock
        dock.playClicked.connect(controller.play)
        dock.pauseClicked.connect(controller.pause)
        dock.stopClicked.connect(controller.stop)
        dock.previousClicked.connect(controller.previous_frame)
        dock.nextClicked.connect(controller.next_frame)
        dock.speedChanged.connect(controller.set_speed)
        dock.loopChanged.connect(controller.set_loop)
        dock.frameSeeked.connect(controller.seek)
        # Camera reset is viewport-local (fit + center), not an external viewer launch.
        dock.resetCameraClicked.connect(self.viewer_canvas.reset_camera)

    def show_loading(self, message: str | None) -> None:
        if message:
            self._overlay.show_message(message)
        else:
            self._overlay.hide_overlay()

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
        """No-op - inspector removed; data lives in status / session context."""

    def set_inspector_metrics(self, metrics: dict) -> None:
        """No-op - inspector removed."""

    def set_inspector_dataset(self, fields: dict) -> None:
        """No-op - inspector removed."""

    def set_inspector_playback(self, fields: dict) -> None:
        """No-op - inspector removed."""

    def update_status(self, snapshot: StatusSnapshot) -> None:
        self.status.update_snapshot(snapshot)

    def show_error(self, title: str, message: str) -> None:
        if self._stack.currentIndex() == 0 and title.lower().startswith("dataset"):
            QMessageBox.critical(self, title, message)
            return
        self._error_banner.show_error(title, message)
        self.status.showMessage(f"{title}: {message}", 8000)

    def _open_dataset_dialog(self) -> None:
        dialog = OpenProjectDialog(self.settings.dataset_path, self)
        if dialog.exec():
            path = dialog.selected_path()
            if self.controller is not None:
                self.controller.open_dataset(str(path) if path else None)

    def _open_settings(self) -> None:
        SettingsDialog(self.settings, self).exec()

    def _open_about(self) -> None:
        AboutDialog(self).exec()

    def closeEvent(self, event) -> None:  # noqa: N802
        self.settings.window_width = self.width()
        self.settings.window_height = self.height()
        self.settings.save()
        if self.controller is not None:
            self.controller.shutdown()
        super().closeEvent(event)

    def resizeEvent(self, event) -> None:  # noqa: N802
        self._overlay.setGeometry(self.rect())
        super().resizeEvent(event)
