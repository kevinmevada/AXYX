"""Animation events / callbacks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

EventCallback = Callable[["AnimationEvent", float], None]


@dataclass(frozen=True, slots=True)
class AnimationEvent:
    """Timed event fired during playback (Footstep, Jump, Land, custom)."""

    name: str
    time: float
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(self, "time", float(self.time))
        object.__setattr__(self, "payload", dict(self.payload))


@dataclass
class EventDispatcher:
    """Dispatch clip events crossed while the clock advances."""

    listeners: dict[str, list[EventCallback]] = field(default_factory=dict)
    fired: list[AnimationEvent] = field(default_factory=list)

    def on(self, name: str, callback: EventCallback) -> None:
        self.listeners.setdefault(name, []).append(callback)
        self.listeners.setdefault("*", [])

    def clear(self) -> None:
        self.listeners.clear()
        self.fired.clear()

    def dispatch_range(
        self,
        events: tuple[AnimationEvent, ...],
        t0: float,
        t1: float,
        *,
        looped: bool = False,
        duration: float = 0.0,
    ) -> list[AnimationEvent]:
        """Fire events with time in ``(t0, t1]`` (handles simple loop wrap)."""
        hit: list[AnimationEvent] = []
        if not events:
            return hit
        if not looped or t1 >= t0:
            for ev in events:
                if t0 < ev.time <= t1:
                    hit.append(ev)
        else:
            # Wrapped past end → start.
            for ev in events:
                if ev.time > t0 or ev.time <= t1:
                    hit.append(ev)
        for ev in hit:
            self.fired.append(ev)
            for cb in self.listeners.get(ev.name, ()):
                cb(ev, t1)
            for cb in self.listeners.get("*", ()):
                cb(ev, t1)
        return hit


__all__ = ["AnimationEvent", "EventCallback", "EventDispatcher"]
