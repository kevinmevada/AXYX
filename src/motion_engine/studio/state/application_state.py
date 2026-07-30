"""Shared application state with Qt signals."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal

from motion_engine.studio.models.playback_model import PlaybackState

_UNSET = object()

@dataclass
class ProjectState:
    project_path: str | None = None
    subject_id: str | None = None
    session_name: str | None = None

@dataclass
class SelectionState:
    subject_id: str | None = None
    session_name: str | None = None

@dataclass
class WorkspaceState:
    preset_name: str | None = None
    explorer_visible: bool = True
    inspector_visible: bool = True
    charts_visible: bool = True

@dataclass
class ViewportState:
    avatar_enabled: bool = True
    camera_preset: str | None = None

@dataclass
class InspectorState:
    last_tab: str | None = None
    dirty: bool = False

@dataclass
class PlaybackSnapshot:
    playback_state: PlaybackState = PlaybackState.STOPPED
    frame: int = 0
    frame_count: int = 0
    fps: float = 100.0
    playing: bool = False

@dataclass
class ViewState:
    avatar_enabled: bool = True
    sidebar_expanded: bool = True

class ApplicationState(QObject):
    """Lightweight observable state for cross-panel sync."""

    changed = Signal()
    projectChanged = Signal()
    playbackChanged = Signal()
    viewChanged = Signal()
    selectionChanged = Signal()
    workspaceChanged = Signal()
    viewportChanged = Signal()
    inspectorChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.project = ProjectState()
        self.selection = SelectionState()
        self.workspace = WorkspaceState()
        self.viewport = ViewportState()
        self.inspector = InspectorState()
        self.playback = PlaybackSnapshot()
        self.view = ViewState()

    def _sync_selection_from_project(self) -> None:
        self.selection.subject_id = self.project.subject_id
        self.selection.session_name = self.project.session_name

    def _sync_project_from_selection(self) -> None:
        self.project.subject_id = self.selection.subject_id
        self.project.session_name = self.selection.session_name

    def set_project(
        self,
        *,
        project_path: str | None = None,
        subject_id: str | None = None,
        session_name: str | None = None,
    ) -> None:
        if project_path is not None:
            self.project.project_path = project_path
        if subject_id is not None:
            self.project.subject_id = subject_id
        if session_name is not None:
            self.project.session_name = session_name
        self._sync_selection_from_project()
        self.projectChanged.emit()
        self.selectionChanged.emit()
        self.changed.emit()

    def set_selection(
        self,
        *,
        subject_id: str | None = None,
        session_name: str | None = None,
    ) -> None:
        if subject_id is not None:
            self.selection.subject_id = subject_id
        if session_name is not None:
            self.selection.session_name = session_name
        self._sync_project_from_selection()
        self.selectionChanged.emit()
        self.projectChanged.emit()
        self.changed.emit()

    def set_workspace(
        self,
        *,
        preset_name: str | None | object = _UNSET,
        explorer_visible: bool | None = None,
        inspector_visible: bool | None = None,
        charts_visible: bool | None = None,
    ) -> None:
        if preset_name is not _UNSET:
            self.workspace.preset_name = preset_name  # type: ignore[assignment]
        if explorer_visible is not None:
            self.workspace.explorer_visible = explorer_visible
        if inspector_visible is not None:
            self.workspace.inspector_visible = inspector_visible
        if charts_visible is not None:
            self.workspace.charts_visible = charts_visible
        self.workspaceChanged.emit()
        self.changed.emit()

    def set_viewport(
        self,
        *,
        avatar_enabled: bool | None = None,
        camera_preset: str | None = None,
    ) -> None:
        if avatar_enabled is not None:
            self.viewport.avatar_enabled = avatar_enabled
        if camera_preset is not None:
            self.viewport.camera_preset = camera_preset
        self.viewportChanged.emit()
        self.changed.emit()

    def set_inspector(
        self,
        *,
        last_tab: str | None = None,
        dirty: bool | None = None,
    ) -> None:
        if last_tab is not None:
            self.inspector.last_tab = last_tab
        if dirty is not None:
            self.inspector.dirty = dirty
        self.inspectorChanged.emit()
        self.changed.emit()

    def set_playback(
        self,
        *,
        playback_state: PlaybackState | None = None,
        frame: int | None = None,
        frame_count: int | None = None,
        fps: float | None = None,
        playing: bool | None = None,
    ) -> None:
        if playback_state is not None:
            self.playback.playback_state = playback_state
        if frame is not None:
            self.playback.frame = frame
        if frame_count is not None:
            self.playback.frame_count = frame_count
        if fps is not None:
            self.playback.fps = fps
        if playing is not None:
            self.playback.playing = playing
        self.playbackChanged.emit()
        self.changed.emit()

    def set_view(self, *, avatar_enabled: bool | None = None, sidebar_expanded: bool | None = None) -> None:
        if avatar_enabled is not None:
            self.view.avatar_enabled = avatar_enabled
            self.viewport.avatar_enabled = avatar_enabled
        if sidebar_expanded is not None:
            self.view.sidebar_expanded = sidebar_expanded
            self.workspace.explorer_visible = sidebar_expanded
        self.viewChanged.emit()
        if avatar_enabled is not None:
            self.viewportChanged.emit()
        if sidebar_expanded is not None:
            self.workspaceChanged.emit()
        self.changed.emit()

