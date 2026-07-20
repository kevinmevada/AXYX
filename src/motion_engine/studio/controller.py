"""Studio controller - UI event orchestration without owning widgets.

The controller coordinates services and updates the main window through a
narrow view protocol so rendering backends can change without touching
transport logic.
"""

from __future__ import annotations

import logging
import time
from typing import Protocol

from PySide6.QtCore import QObject, QTimer

from motion_engine.studio.models.playback_model import PlaybackModel
from motion_engine.studio.models.session_model import SessionModel
from motion_engine.studio.models.subject_model import SubjectModel
from motion_engine.studio.services.analytics_service import AnalyticsService
from motion_engine.studio.services.motion_service import MotionService, MotionServiceError
from motion_engine.studio.services.playback_service import PlaybackService
from motion_engine.studio.services.project_service import ProjectService
from motion_engine.studio.services.renderer_service import RendererService
from motion_engine.studio.settings import StudioSettings
from motion_engine.studio.widgets.status_bar import StatusSnapshot

logger = logging.getLogger(__name__)


class StudioView(Protocol):
    """Minimal view surface required by :class:`StudioController`."""

    def show_welcome(self, visible: bool) -> None: ...

    def show_loading(self, message: str | None) -> None: ...

    def set_subjects(self, subjects: list[SubjectModel]) -> None: ...

    def set_sessions(self, subject_id: str, sessions: list[SessionModel]) -> None: ...

    def clear_sessions(self) -> None: ...

    def set_recent_sessions(self, keys: list[str]) -> None: ...

    def set_skeleton_preview(self, skeleton, frame: int) -> None: ...

    def sync_playback(self, model: PlaybackModel) -> None: ...

    def set_inspector_clinical(self, fields: dict) -> None: ...

    def set_inspector_metrics(self, metrics: dict) -> None: ...

    def set_inspector_dataset(self, fields: dict) -> None: ...

    def set_inspector_playback(self, fields: dict) -> None: ...

    def update_status(self, snapshot: StatusSnapshot) -> None: ...

    def show_error(self, title: str, message: str) -> None: ...


class StudioController(QObject):
    """Application controller for AXYX.

    Args:
        view: Main window implementing :class:`StudioView`.
        project_service: Project open/close service.
        motion_service: Dataset/skeleton/clip service.
        playback_service: Transport service.
        analytics_service: Metrics service.
        renderer: Swappable viewer backend.
        settings: Persistent settings.
    """

    def __init__(
        self,
        view: StudioView,
        project_service: ProjectService,
        motion_service: MotionService,
        playback_service: PlaybackService,
        analytics_service: AnalyticsService,
        renderer: RendererService,
        settings: StudioSettings,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.view = view
        self.project = project_service
        self.motion = motion_service
        self.playback = playback_service
        self.analytics = analytics_service
        self.renderer = renderer
        self.settings = settings
        self._subjects: list[SubjectModel] = []
        self._sessions: list[SessionModel] = []
        self._active_subject: str | None = None
        self._active_session: SessionModel | None = None
        self._last_tick = time.perf_counter()

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    # ------------------------------------------------------------------ boot

    def start(self) -> None:
        """Initialize UI for first run."""
        self.view.show_welcome(True)
        self.view.set_recent_sessions(self.settings.recent_sessions)
        self.view.set_inspector_dataset(
            self.analytics.dataset_info(subject_count=0, dataset_path=None)
        )
        self._refresh_status()

    def open_default_dataset(self) -> None:
        """Open the default / configured dataset."""
        self.view.show_loading("Loading MotionDatabase...")
        try:
            model = self.project.open_default()
            self._subjects = self.motion.list_subjects(
                pinned=set(self.settings.pinned_subjects)
            )
            self.view.set_subjects(self._subjects)
            self.view.show_welcome(False)
            self.view.set_inspector_dataset(
                self.analytics.dataset_info(
                    subject_count=model.subject_count,
                    dataset_path=str(model.dataset_path) if model.dataset_path else None,
                )
            )
            self._refresh_status()
        except MotionServiceError as exc:
            logger.exception("Failed to open dataset")
            self.view.show_error("Dataset Error", str(exc))
        finally:
            self.view.show_loading(None)

    def open_dataset(self, path: str | None) -> None:
        """Open a dataset path (``None`` = default)."""
        self.view.show_loading("Loading MotionDatabase...")
        try:
            model = self.project.open(path)
            self._subjects = self.motion.list_subjects(
                pinned=set(self.settings.pinned_subjects)
            )
            self.view.set_subjects(self._subjects)
            self.view.show_welcome(False)
            self.view.clear_sessions()
            self.view.set_inspector_dataset(
                self.analytics.dataset_info(
                    subject_count=model.subject_count,
                    dataset_path=str(model.dataset_path) if model.dataset_path else None,
                )
            )
            self._refresh_status()
        except MotionServiceError as exc:
            logger.exception("Failed to open dataset path=%s", path)
            self.view.show_error("Dataset Error", str(exc))
        finally:
            self.view.show_loading(None)

    # ------------------------------------------------------------- selection

    def select_subject(self, subject_id: str) -> None:
        """Load sessions for ``subject_id``."""
        try:
            self._sessions = self.motion.list_sessions(subject_id)
            self._active_subject = subject_id
            self.settings.remember_subject(subject_id)
            self.view.set_sessions(subject_id, self._sessions)
            subject = next((s for s in self._subjects if s.subject_id == subject_id), None)
            if subject is not None:
                self.view.set_inspector_clinical(subject.to_dict())
            self._refresh_status()
        except MotionServiceError as exc:
            self.view.show_error("Subject Error", str(exc))

    def select_session(self, session_name: str) -> None:
        """Build skeleton/clip for the active subject session."""
        if not self._active_subject:
            return
        self.view.show_loading(f"Building skeleton for {self._active_subject}/{session_name}...")
        try:
            skeleton, clip = self.motion.load_session(self._active_subject, session_name)
            session_model = next(
                (s for s in self._sessions if s.name == session_name), None
            )
            self._active_session = session_model
            fps = float(
                skeleton.sampling_rate_hz
                or (clip.fps if clip is not None else 100.0)
                or 100.0
            )
            self.playback.configure(
                frame_count=skeleton.frame_count,
                fps=fps,
                subject_id=self._active_subject,
                session_name=session_name,
                speed=self.settings.playback_speed,
                loop=self.settings.loop_playback,
            )
            self.view.set_skeleton_preview(skeleton, 0)
            self.view.sync_playback(self.playback.model)
            if session_model is not None:
                overview = self.analytics.session_overview(session_model)
                self.view.set_inspector_clinical(overview)
                self.view.set_inspector_metrics(session_model.metrics)
            self.view.set_inspector_playback(self.playback.model.to_dict())
            self.settings.remember_session(self._active_subject, session_name)
            self.view.set_recent_sessions(self.settings.recent_sessions)
            # Always keep visualization inside the app UI.
            self.renderer.show_skeleton(skeleton)
            self._refresh_status()
        except MotionServiceError as exc:
            logger.exception("Session load failed")
            self.view.show_error("Session Error", str(exc))
        finally:
            self.view.show_loading(None)

    def select_recent(self, key: str) -> None:
        """Handle ``subject/session`` recent shortcut."""
        if "/" not in key:
            return
        subject_id, session_name = key.split("/", 1)
        self.select_subject(subject_id)
        self.select_session(session_name)

    # -------------------------------------------------------------- playback

    def play(self) -> None:
        self.playback.play()
        self._sync_playback_ui()

    def pause(self) -> None:
        self.playback.pause()
        self._sync_playback_ui()

    def stop(self) -> None:
        self.playback.stop()
        self._apply_frame()
        self._sync_playback_ui()

    def next_frame(self) -> None:
        self.playback.next_frame()
        self._apply_frame()
        self._sync_playback_ui()

    def previous_frame(self) -> None:
        self.playback.previous_frame()
        self._apply_frame()
        self._sync_playback_ui()

    def seek(self, frame: int) -> None:
        self.playback.seek(frame)
        self._apply_frame()
        self._sync_playback_ui()

    def set_speed(self, speed: float) -> None:
        self.playback.set_speed(speed)
        self.settings.playback_speed = speed
        self.settings.save()
        self._sync_playback_ui()

    def set_loop(self, enabled: bool) -> None:
        self.playback.set_loop(enabled)
        self.settings.loop_playback = enabled
        self.settings.save()
        self._sync_playback_ui()

    def open_motion_viewer(self) -> None:
        """Focus / reset the embedded Motion Engine viewport."""
        skeleton = self.motion.skeleton
        if skeleton is None:
            self.view.show_error("Viewer", "Load a session before using the motion viewport.")
            return
        try:
            self.renderer.show_skeleton(skeleton)
            self.renderer.reset_camera()
            self.renderer.set_frame(self.playback.model.current_frame)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Renderer failed")
            self.view.show_error("Viewer Error", str(exc))

    def shutdown(self) -> None:
        """Release renderer resources."""
        self.renderer.close()

    # ----------------------------------------------------------------- ticks

    def _on_tick(self) -> None:
        now = time.perf_counter()
        dt = now - self._last_tick
        self._last_tick = now
        if self.playback.tick(dt):
            self._apply_frame()
            self._sync_playback_ui()

    def _apply_frame(self) -> None:
        skeleton = self.motion.skeleton
        frame = self.playback.model.current_frame
        if skeleton is not None:
            self.view.set_skeleton_preview(skeleton, frame)
            self.renderer.set_frame(frame)

    def _sync_playback_ui(self) -> None:
        self.view.sync_playback(self.playback.model)
        self.view.set_inspector_playback(self.playback.model.to_dict())
        self._refresh_status()

    def _refresh_status(self) -> None:
        model = self.playback.model
        dataset = "-"
        if self.project.model.dataset_path is not None:
            dataset = self.project.model.dataset_path.name
        self.view.update_status(
            StatusSnapshot(
                dataset=dataset,
                subject=model.subject_id or self._active_subject or "-",
                session=model.session_name or "-",
                frames=model.frame_count,
                current_frame=model.current_frame,
                fps=model.fps,
                duration_sec=model.duration_sec,
                playback_state=model.state.value,
            )
        )
