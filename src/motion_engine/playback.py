"""
Playback controller interfaces for the Visualization Engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from motion_engine.timeline import Timeline


class PlaybackState(str, Enum):
    """Playback finite-state machine."""

    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


@dataclass(slots=True)
class PlaybackController:
    """Frame playback state machine (renderer-independent)."""

    timeline: Timeline
    state: PlaybackState = PlaybackState.STOPPED
    speed: float = 1.0
    loop: bool = True
    reverse: bool = False

    def play(self) -> None:
        """Start or resume playback."""
        self.state = PlaybackState.PLAYING

    def pause(self) -> None:
        """Pause playback, preserving the playhead."""
        if self.state is PlaybackState.PLAYING:
            self.state = PlaybackState.PAUSED

    def stop(self) -> None:
        """Stop and rewind to frame 0."""
        self.state = PlaybackState.STOPPED
        self.timeline.seek(0)

    def set_speed(self, speed: float) -> None:
        """Set playback speed multiplier (1.0 = realtime)."""
        if speed == 0.0:
            raise ValueError("speed must be non-zero")
        self.speed = float(speed)
        self.reverse = speed < 0.0

    def step(self, delta_frames: int = 1) -> int:
        """Advance the playhead by ``delta_frames`` (honors reverse/loop)."""
        if self.timeline.n_frames <= 0:
            return 0
        step = -abs(delta_frames) if self.reverse else abs(delta_frames)
        nxt = self.timeline.current_frame + step
        if self.loop:
            nxt %= self.timeline.n_frames
        else:
            nxt = max(0, min(nxt, self.timeline.n_frames - 1))
            if nxt in {0, self.timeline.n_frames - 1} and self.state is PlaybackState.PLAYING:
                # Soft-stop at ends when not looping.
                pass
        return self.timeline.seek(nxt)

    # TODO: audio sync, shuttle scrub, segment looping.
