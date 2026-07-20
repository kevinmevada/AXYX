"""Playback state model shared by UI and services."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PlaybackState(str, Enum):
    """Playback transport state."""

    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


@dataclass
class PlaybackModel:
    """Transport / timeline state for the active session.

    Attributes:
        state: Current transport state.
        current_frame: Zero-based frame index.
        frame_count: Total frames.
        fps: Sampling rate used for timing.
        speed: Playback rate multiplier.
        loop: Whether looping is enabled.
        duration_sec: Clip duration.
        current_time_sec: Playhead time.
    """

    state: PlaybackState = PlaybackState.STOPPED
    current_frame: int = 0
    frame_count: int = 0
    fps: float = 100.0
    speed: float = 1.0
    loop: bool = True
    duration_sec: float = 0.0
    current_time_sec: float = 0.0
    subject_id: str | None = None
    session_name: str | None = None

    def reset(self) -> None:
        """Reset transport to an empty stop state."""
        self.state = PlaybackState.STOPPED
        self.current_frame = 0
        self.frame_count = 0
        self.fps = 100.0
        self.speed = 1.0
        self.loop = True
        self.duration_sec = 0.0
        self.current_time_sec = 0.0
        self.subject_id = None
        self.session_name = None

    def configure(
        self,
        *,
        frame_count: int,
        fps: float,
        subject_id: str | None = None,
        session_name: str | None = None,
    ) -> None:
        """Configure transport for a newly loaded session."""
        self.frame_count = max(0, int(frame_count))
        self.fps = float(fps) if fps > 0 else 100.0
        self.current_frame = 0
        self.current_time_sec = 0.0
        self.duration_sec = (
            (self.frame_count - 1) / self.fps if self.frame_count > 1 else 0.0
        )
        self.state = PlaybackState.STOPPED
        self.subject_id = subject_id
        self.session_name = session_name

    def seek(self, frame: int) -> None:
        """Seek to a clamped frame index."""
        if self.frame_count <= 0:
            self.current_frame = 0
            self.current_time_sec = 0.0
            return
        self.current_frame = max(0, min(int(frame), self.frame_count - 1))
        self.current_time_sec = self.current_frame / self.fps

    def step(self, delta: int = 1) -> None:
        """Advance by ``delta`` frames, honoring loop."""
        if self.frame_count <= 0:
            return
        nxt = self.current_frame + int(delta)
        if self.loop:
            nxt %= self.frame_count
        else:
            nxt = max(0, min(nxt, self.frame_count - 1))
        self.seek(nxt)

    def to_dict(self) -> dict[str, Any]:
        """Serialize playback status."""
        return {
            "state": self.state.value,
            "current_frame": self.current_frame,
            "frame_count": self.frame_count,
            "fps": self.fps,
            "speed": self.speed,
            "loop": self.loop,
            "duration_sec": self.duration_sec,
            "current_time_sec": self.current_time_sec,
            "subject_id": self.subject_id,
            "session_name": self.session_name,
        }
