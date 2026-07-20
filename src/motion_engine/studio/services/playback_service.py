"""Playback transport service for AXYX."""

from __future__ import annotations

import logging

from motion_engine.studio.models.playback_model import PlaybackModel, PlaybackState

logger = logging.getLogger(__name__)


class PlaybackService:
    """Mutate :class:`PlaybackModel` in response to transport commands.

    Example:
        >>> service = PlaybackService(PlaybackModel())
        >>> service.configure(frame_count=100, fps=100.0)
        >>> service.play()
    """

    def __init__(self, model: PlaybackModel | None = None) -> None:
        self.model = model or PlaybackModel()

    def configure(
        self,
        *,
        frame_count: int,
        fps: float,
        subject_id: str | None = None,
        session_name: str | None = None,
        speed: float | None = None,
        loop: bool | None = None,
    ) -> PlaybackModel:
        """Configure transport for a loaded session."""
        self.model.configure(
            frame_count=frame_count,
            fps=fps,
            subject_id=subject_id,
            session_name=session_name,
        )
        if speed is not None:
            self.set_speed(speed)
        if loop is not None:
            self.set_loop(loop)
        return self.model

    def play(self) -> PlaybackModel:
        """Start or resume playback."""
        if self.model.frame_count <= 0:
            return self.model
        self.model.state = PlaybackState.PLAYING
        logger.debug("Playback started frame=%s", self.model.current_frame)
        return self.model

    def pause(self) -> PlaybackModel:
        """Pause playback."""
        if self.model.state == PlaybackState.PLAYING:
            self.model.state = PlaybackState.PAUSED
        return self.model

    def stop(self) -> PlaybackModel:
        """Stop and rewind to frame 0."""
        self.model.state = PlaybackState.STOPPED
        self.model.seek(0)
        return self.model

    def seek(self, frame: int) -> PlaybackModel:
        """Seek to an absolute frame."""
        self.model.seek(frame)
        return self.model

    def next_frame(self) -> PlaybackModel:
        """Advance one frame."""
        self.model.step(1)
        return self.model

    def previous_frame(self) -> PlaybackModel:
        """Rewind one frame."""
        self.model.step(-1)
        return self.model

    def set_speed(self, speed: float) -> PlaybackModel:
        """Set playback speed multiplier."""
        self.model.speed = max(0.05, float(speed))
        return self.model

    def set_loop(self, enabled: bool) -> PlaybackModel:
        """Enable or disable looping."""
        self.model.loop = bool(enabled)
        return self.model

    def tick(self, dt_sec: float) -> bool:
        """Advance playhead by wall-clock ``dt_sec`` while playing.

        Returns:
            True if the frame index changed.
        """
        if self.model.state != PlaybackState.PLAYING or self.model.frame_count <= 0:
            return False
        before = self.model.current_frame
        frames = dt_sec * self.model.fps * self.model.speed
        if abs(frames) < 1e-9:
            return False
        # Accumulate via time then convert to nearest step.
        target_time = self.model.current_time_sec + dt_sec * self.model.speed
        if self.model.loop and self.model.duration_sec > 0:
            target_time %= self.model.duration_sec + (1.0 / self.model.fps)
        frame = int(round(target_time * self.model.fps))
        self.model.seek(frame)
        return self.model.current_frame != before
