"""
Timeline model for frame-accurate playback.

Architecture-only helpers used by playback / animation controllers.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Timeline:
    """Logical timeline over discrete skeleton frames."""

    n_frames: int
    sampling_rate_hz: float = 100.0
    current_frame: int = 0

    def __post_init__(self) -> None:
        if self.n_frames < 0:
            raise ValueError("n_frames must be >= 0")
        if self.sampling_rate_hz <= 0:
            raise ValueError("sampling_rate_hz must be > 0")
        self.current_frame = max(0, min(self.current_frame, max(self.n_frames - 1, 0)))

    @property
    def duration_seconds(self) -> float:
        """Total duration in seconds."""
        if self.n_frames <= 0:
            return 0.0
        return (self.n_frames - 1) / self.sampling_rate_hz

    @property
    def current_time_seconds(self) -> float:
        """Current playhead time in seconds."""
        return self.current_frame / self.sampling_rate_hz

    def seek(self, frame: int) -> int:
        """Clamp and set the playhead frame index."""
        if self.n_frames <= 0:
            self.current_frame = 0
            return 0
        self.current_frame = max(0, min(int(frame), self.n_frames - 1))
        return self.current_frame

    def seek_time(self, seconds: float) -> int:
        """Seek using a time in seconds."""
        return self.seek(int(round(seconds * self.sampling_rate_hz)))

    # TODO: markers, regions of interest, event annotations on the timeline.
