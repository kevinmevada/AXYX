"""Timeline — play / pause / seek / loop / reverse / frame step."""

from __future__ import annotations

from dataclasses import dataclass, field

from motion_engine.rendering.avatar.animation.clock import AnimationClock
from motion_engine.rendering.avatar.animation.looping import wrap_time
from motion_engine.rendering.avatar.animation.types import LoopMode, PlaybackState


@dataclass
class Timeline:
    """Clip timeline controller backed by :class:`AnimationClock`."""

    duration: float = 0.0
    fps: float = 30.0
    loop_mode: LoopMode = LoopMode.LOOP
    state: PlaybackState = PlaybackState.STOPPED
    clock: AnimationClock = field(default_factory=AnimationClock)
    finished: bool = False
    _reverse_sign: float = 1.0

    @property
    def time(self) -> float:
        return self.clock.time

    @property
    def speed(self) -> float:
        return self.clock.speed

    @property
    def frame(self) -> int:
        fps = self.fps if self.fps > 0 else 30.0
        return int(round(self.sample_time() * fps))

    def play(self) -> None:
        self.state = PlaybackState.PLAYING
        self.clock.resume()
        self.finished = False

    def pause(self) -> None:
        self.state = PlaybackState.PAUSED
        self.clock.pause()

    def resume(self) -> None:
        if self.state is PlaybackState.PAUSED:
            self.play()

    def stop(self) -> None:
        self.state = PlaybackState.STOPPED
        self.clock.pause()
        self.clock.reset(0.0)
        self.finished = False
        self._reverse_sign = 1.0

    def seek(self, time: float) -> float:
        wrapped, finished = wrap_time(time, self.duration, self.loop_mode)
        self.clock.seek(wrapped)
        self.finished = finished and self.loop_mode is LoopMode.ONCE
        return wrapped

    def set_speed(self, speed: float) -> None:
        self.clock.set_speed(speed)

    def set_loop(self, mode: LoopMode) -> None:
        self.loop_mode = mode

    def reverse(self) -> None:
        self._reverse_sign *= -1.0
        self.clock.set_speed(abs(self.clock.speed) * self._reverse_sign)

    def step_frames(self, frames: int = 1) -> float:
        fps = self.fps if self.fps > 0 else 30.0
        return self.seek(self.clock.time + float(frames) / fps)

    def tick(self, dt: float) -> float:
        if self.state is not PlaybackState.PLAYING:
            return self.sample_time()
        raw = self.clock.tick(dt)
        wrapped, finished = wrap_time(raw, self.duration, self.loop_mode)
        if self.loop_mode is LoopMode.ONCE and finished:
            self.clock.seek(self.duration)
            self.finished = True
            self.state = PlaybackState.STOPPED
            self.clock.pause()
            return self.duration
        if self.loop_mode is not LoopMode.ONCE:
            # Keep clock in-range for LOOP / PING_PONG.
            self.clock.seek(wrapped)
        return wrapped

    def sample_time(self) -> float:
        wrapped, _ = wrap_time(self.clock.time, self.duration, self.loop_mode)
        return wrapped


__all__ = ["Timeline"]
