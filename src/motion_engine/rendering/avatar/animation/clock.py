"""Animation clock — variable delta time source."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AnimationClock:
    """Monotonic playback clock in seconds."""

    time: float = 0.0
    speed: float = 1.0
    paused: bool = False

    def reset(self, time: float = 0.0) -> None:
        self.time = float(time)

    def set_speed(self, speed: float) -> None:
        self.speed = float(speed)

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        self.paused = False

    def tick(self, dt: float) -> float:
        """Advance by ``dt`` wall seconds scaled by speed. Returns new time."""
        if not self.paused:
            self.time += float(dt) * self.speed
        return self.time

    def seek(self, time: float) -> float:
        self.time = float(time)
        return self.time


__all__ = ["AnimationClock"]
