"""Frame scheduler — advances playback time / indices."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RuntimeScheduler:
    """Deterministic frame/time advancement for research playback."""

    fps: float = 30.0
    frame_index: int = 0
    time_sec: float = 0.0
    playing: bool = False
    loop: bool = True
    speed: float = 1.0
    frame_count: int = 0

    def reset(self) -> None:
        self.frame_index = 0
        self.time_sec = 0.0
        self.playing = False

    def play(self) -> None:
        self.playing = True

    def pause(self) -> None:
        self.playing = False

    def seek(self, index: int) -> None:
        if self.frame_count <= 0:
            self.frame_index = 0
            self.time_sec = 0.0
            return
        idx = int(index) % self.frame_count if self.loop else max(0, min(int(index), self.frame_count - 1))
        self.frame_index = idx
        self.time_sec = idx / max(self.fps, 1e-6)

    def tick(self, dt: float | None = None) -> int:
        if not self.playing or self.frame_count <= 0:
            return self.frame_index
        step = dt if dt is not None else (1.0 / max(self.fps, 1e-6))
        self.time_sec += float(step) * float(self.speed)
        idx = int(self.time_sec * self.fps)
        if self.loop:
            idx = idx % self.frame_count
            self.time_sec = idx / max(self.fps, 1e-6)
        else:
            if idx >= self.frame_count:
                idx = self.frame_count - 1
                self.playing = False
        self.frame_index = idx
        return self.frame_index


__all__ = ["RuntimeScheduler"]
