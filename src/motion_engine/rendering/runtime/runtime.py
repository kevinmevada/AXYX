"""DigitalTwinRuntime — unified Phase 1 research platform entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from motion_engine.rendering.runtime.constants import (
    EVENT_AVATAR,
    EVENT_FRAME,
    EVENT_SUBJECT,
    EVENT_TRIAL,
    RUNTIME_VERSION,
)
from motion_engine.rendering.runtime.exceptions import RuntimeStateError
from motion_engine.rendering.runtime.runtime_configuration import (
    RuntimeConfiguration,
    get_preset,
)
from motion_engine.rendering.runtime.runtime_context import RuntimeContext
from motion_engine.rendering.runtime.runtime_manager import RuntimeManager
from motion_engine.rendering.runtime.runtime_session import RuntimeSession
from motion_engine.rendering.runtime.types import (
    AvatarKind,
    PipelineFrame,
    PlaybackMode,
    RuntimePhase,
    RuntimeReport,
)


class DigitalTwinRuntime:
    """One-click clinical motion → avatar → skinning research runtime.

    Composes frozen M1–M6 public APIs. Does not modify skeleton, pose,
    skinning, animation, retarget, viewer, or studio public surfaces.
    """

    def __init__(self, config: RuntimeConfiguration | None = None) -> None:
        self.manager = RuntimeManager(config)
        self.session = RuntimeSession(config=self.manager.config)
        self.context: RuntimeContext | None = None

    @property
    def version(self) -> str:
        return RUNTIME_VERSION

    @property
    def phase(self) -> RuntimePhase:
        return self.manager.state.phase

    @property
    def config(self) -> RuntimeConfiguration:
        return self.manager.config

    def startup(self) -> None:
        self.manager.startup()
        cfg = self.config
        if cfg.database_path:
            self.load_database(cfg.database_path)
        if cfg.subject_id:
            self.select_subject(cfg.subject_id)
        if cfg.trial_id:
            self.select_trial(cfg.trial_id)
        if cfg.avatar:
            self.select_avatar(cfg.avatar)

    def shutdown(self) -> None:
        self.context = None
        self.manager.shutdown()

    def load_database(self, path: str | Path) -> bool:
        db = self.manager.pipeline.load_database(str(path))
        ok = db is not None
        self.manager.logger.research(
            f"database_loaded={ok}",
            path=str(path),
        )
        return ok

    def list_subjects(self) -> list[str]:
        return self.manager.pipeline.list_subjects()

    def list_trials(self, subject_id: str | None = None) -> list[str]:
        sid = subject_id or self.session.subject_id
        if not sid:
            return []
        return self.manager.pipeline.list_trials(sid)

    def select_subject(self, subject_id: str) -> None:
        self.session.subject_id = subject_id
        self.manager.events.emit(EVENT_SUBJECT, subject_id=subject_id)
        self.manager.logger.research(f"subject={subject_id}")

    def select_trial(self, trial_id: str) -> None:
        """Select motion trial (MotionDatabase session name)."""
        self.session.trial_id = trial_id
        self.manager.events.emit(EVENT_TRIAL, trial_id=trial_id)
        self.manager.logger.research(f"trial={trial_id}")

    # Alias for clinical terminology
    select_session = select_trial

    def select_avatar(self, avatar: str | AvatarKind) -> None:
        kind = AvatarKind(avatar) if isinstance(avatar, str) else avatar
        self.session.avatar_kind = kind
        self.session.avatar_name = kind.value
        self.manager.events.emit(EVENT_AVATAR, avatar=kind.value)
        self.manager.logger.research(f"avatar={kind.value}")

    def select_mapping(self, profile: str) -> None:
        self.session.mapping_profile = profile
        self.manager.config.mapping_profile = profile

    def set_playback_mode(self, mode: str | PlaybackMode) -> None:
        self.session.playback_mode = PlaybackMode(mode) if isinstance(mode, str) else mode

    def prepare(self) -> RuntimeContext:
        if self.phase == RuntimePhase.UNINITIALIZED:
            raise RuntimeStateError("Call startup() before prepare()")
        self.session.mapping_profile = self.session.mapping_profile or self.config.mapping_profile
        self.session.playback_mode = self.session.playback_mode
        self.session.config = self.config
        try:
            ctx = self.manager.pipeline.prepare(self.session, self.config)
            report = self.manager.validator.validate_context(ctx, RuntimePhase.PREPARED)
            if not report.ok:
                raise RuntimeStateError(f"Prepare validation failed: {report.errors}")
            self.context = ctx
            self.manager.scheduler.frame_count = max(1, len(ctx.motion_poses) or 1)
            if ctx.session.playback_mode == PlaybackMode.ANIMATION:
                player = ctx.extras.get("anim_player")
                if player and player.clip:
                    self.manager.scheduler.frame_count = max(
                        1, int(player.clip.duration * self.config.fps)
                    )
            self.manager.scheduler.reset()
            self.manager.state.transition(RuntimePhase.PREPARED, force=True)
            self.manager.logger.info(
                f"prepared avatar={self.session.avatar_name} "
                f"mode={self.session.playback_mode.value} "
                f"frames={self.manager.scheduler.frame_count}"
            )
            return ctx
        except Exception as exc:  # noqa: BLE001
            self.manager.fail(exc)
            raise

    def play(self) -> None:
        if self.context is None:
            self.prepare()
        self.manager.scheduler.play()
        self.manager.state.transition(RuntimePhase.PLAYING, force=True)

    def pause(self) -> None:
        self.manager.scheduler.pause()
        self.manager.state.transition(RuntimePhase.PAUSED, force=True)

    def stop(self) -> None:
        self.manager.scheduler.pause()
        self.manager.scheduler.seek(0)
        self.manager.state.transition(RuntimePhase.STOPPED, force=True)

    def seek(self, frame_index: int) -> PipelineFrame:
        self.manager.scheduler.seek(frame_index)
        return self._process_current()

    def tick(self, dt: float | None = None) -> PipelineFrame:
        if self.phase not in {RuntimePhase.PLAYING, RuntimePhase.PREPARED, RuntimePhase.PAUSED}:
            if self.context is None:
                self.prepare()
        if self.phase == RuntimePhase.PLAYING or self.manager.scheduler.playing:
            self.manager.scheduler.tick(dt)
        return self._process_current()

    def run_frames(self, n: int | None = None) -> list[PipelineFrame]:
        """Process N frames (or full clip) without requiring a viewer."""
        if self.context is None:
            self.prepare()
        assert self.context is not None
        count = n if n is not None else self.manager.scheduler.frame_count
        self.play()
        out: list[PipelineFrame] = []
        for i in range(count):
            self.manager.scheduler.seek(i)
            out.append(self._process_current())
        self.stop()
        return out

    def iter_frames(self, n: int | None = None) -> Iterator[PipelineFrame]:
        for fr in self.run_frames(n):
            yield fr

    def _process_current(self) -> PipelineFrame:
        if self.context is None:
            raise RuntimeStateError("Runtime not prepared")
        idx = self.manager.scheduler.frame_index
        frame = self.manager.pipeline.process_frame(
            self.context,
            idx,
            mirror=self.config.mirror,
            validate=self.config.validate_each_frame,
        )
        if self.config.validate_each_frame:
            report = self.manager.validator.validate_frame(self.context)
            if not report.ok:
                raise RuntimeStateError(f"Frame validation failed: {report.errors}")
        self.session.frame_index = frame.index
        self.session.time_sec = frame.time
        self.manager.stats.add(frame)
        self.session.statistics = self.report()
        self.manager.events.emit(EVENT_FRAME, index=frame.index, finite=frame.finite)
        return frame

    def report(self) -> RuntimeReport:
        return self.manager.stats.report(
            memory_mb=self.manager.profiler.memory_mb(),
            phase=self.phase.value,
        )

    def profiler_summary(self) -> dict[str, Any]:
        return self.manager.profiler.summary()

    def one_click(
        self,
        *,
        avatar: str = "fixture",
        mapping: str | None = None,
        frames: int = 30,
        subject: str | None = None,
        trial: str | None = None,
    ) -> RuntimeReport:
        """End-to-end research demo: select → prepare → play → report."""
        self.startup()
        if subject:
            self.select_subject(subject)
        if trial:
            self.select_trial(trial)
        self.select_avatar(avatar)
        if mapping:
            self.select_mapping(mapping)
        elif avatar == "fixture":
            self.select_mapping("test_two_bone")
        self.config.synthetic_frames = max(frames, self.config.synthetic_frames)
        self.prepare()
        self.run_frames(frames)
        rep = self.report()
        self.shutdown()
        return rep


class RuntimeFactory:
    """Construct configured DigitalTwinRuntime instances."""

    def create(self, config: RuntimeConfiguration | None = None) -> DigitalTwinRuntime:
        return DigitalTwinRuntime(config)

    def from_preset(self, name: str) -> DigitalTwinRuntime:
        return DigitalTwinRuntime(get_preset(name))

    def research(self) -> DigitalTwinRuntime:
        return self.from_preset("research")

    def debug(self) -> DigitalTwinRuntime:
        return self.from_preset("debug")

    def benchmark(self) -> DigitalTwinRuntime:
        return self.from_preset("benchmark")


__all__ = ["DigitalTwinRuntime", "RuntimeFactory"]
