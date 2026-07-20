"""Tests for StudioController with a fake view."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from motion_engine.studio.controller import StudioController
from motion_engine.studio.models.playback_model import PlaybackModel, PlaybackState
from motion_engine.studio.models.session_model import SessionModel
from motion_engine.studio.models.subject_model import SubjectModel
from motion_engine.studio.services.analytics_service import AnalyticsService
from motion_engine.studio.services.motion_service import MotionService
from motion_engine.studio.services.playback_service import PlaybackService
from motion_engine.studio.services.project_service import ProjectService
from motion_engine.studio.services.renderer_service import NullRenderer
from motion_engine.studio.settings import StudioSettings
from motion_engine.studio.widgets.status_bar import StatusSnapshot


@dataclass
class FakeView:
    welcome_visible: bool = True
    loading: str | None = None
    subjects: list[SubjectModel] = field(default_factory=list)
    sessions: list[SessionModel] = field(default_factory=list)
    recent: list[str] = field(default_factory=list)
    playback: PlaybackModel | None = None
    status: StatusSnapshot | None = None
    errors: list[tuple[str, str]] = field(default_factory=list)
    skeleton_frames: list[int] = field(default_factory=list)
    clinical: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    dataset: dict[str, Any] = field(default_factory=dict)
    playback_fields: dict[str, Any] = field(default_factory=dict)
    heatmap: Any = None
    ai: Any = None
    comparison: Any = None
    dual: bool = False
    cmp_frames: list[int] = field(default_factory=list)

    def show_welcome(self, visible: bool) -> None:
        self.welcome_visible = visible

    def show_loading(self, message: str | None) -> None:
        self.loading = message

    def set_subjects(self, subjects: list[SubjectModel]) -> None:
        self.subjects = subjects

    def set_sessions(self, subject_id: str, sessions: list[SessionModel]) -> None:
        self.sessions = sessions

    def clear_sessions(self) -> None:
        self.sessions = []

    def set_recent_sessions(self, keys: list[str]) -> None:
        self.recent = keys

    def set_skeleton_preview(self, skeleton, frame: int) -> None:
        self.skeleton_frames.append(frame)

    def sync_playback(self, model: PlaybackModel) -> None:
        self.playback = model

    def set_inspector_clinical(self, fields: dict) -> None:
        self.clinical = fields

    def set_inspector_metrics(self, metrics: dict) -> None:
        self.metrics = metrics

    def set_inspector_dataset(self, fields: dict) -> None:
        self.dataset = fields

    def set_inspector_playback(self, fields: dict) -> None:
        self.playback_fields = fields

    def update_status(self, snapshot: StatusSnapshot) -> None:
        self.status = snapshot

    def show_error(self, title: str, message: str) -> None:
        self.errors.append((title, message))

    def show_info(self, title: str, message: str) -> None:
        self.errors.append((title, message))

    def set_inspector_heatmap(self, result) -> None:
        self.heatmap = result

    def set_inspector_ai(self, report) -> None:
        self.ai = report

    def set_inspector_comparison(self, result) -> None:
        self.comparison = result

    def clear_inspector_comparison(self) -> None:
        self.comparison = None

    def set_comparison_skeleton(self, skeleton, frame: int = 0) -> None:
        self.cmp_frames.append(frame)

    def clear_comparison_viewport(self) -> None:
        self.cmp_frames.clear()

    def set_dual_viewports(self, enabled: bool) -> None:
        self.dual = enabled


def test_controller_dataset_subject_session_flow(tmp_path) -> None:
    settings = StudioSettings(
        organization="AXYXTest",
        application=f"Studio-{tmp_path.name}",
        open_viewer_on_session_select=False,
    )
    view = FakeView()
    motion = MotionService()
    project = ProjectService(motion, settings)
    playback = PlaybackService()
    renderer = NullRenderer()
    controller = StudioController(
        view=view,
        project_service=project,
        motion_service=motion,
        playback_service=playback,
        analytics_service=AnalyticsService(),
        renderer=renderer,
        settings=settings,
    )
    controller._timer.stop()
    controller.start()
    assert view.welcome_visible is True

    controller.open_default_dataset()
    assert view.welcome_visible is False
    assert len(view.subjects) >= 1

    controller.select_subject("S2")
    assert view.sessions
    controller.select_session("WU01")
    assert view.playback is not None
    assert view.playback.frame_count > 0
    assert view.skeleton_frames

    controller.play()
    assert playback.model.state == PlaybackState.PLAYING
    controller.next_frame()
    assert playback.model.current_frame >= 1
    controller.open_motion_viewer()
    assert renderer.shown
    controller.shutdown()
