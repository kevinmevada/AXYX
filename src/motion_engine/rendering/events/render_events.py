"""Loose-coupled rendering events."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger(__name__)

Listener = Callable[[Any], None]


class RenderEvent:
    """Base event — plain class so subclasses can define custom constructors."""

    __slots__ = ("name", "payload")

    def __init__(self, name: str, payload: dict[str, Any] | None = None) -> None:
        self.name = name
        self.payload = payload or {}


class AvatarLoaded(RenderEvent):
    def __init__(self, avatar_name: str, **extra: Any) -> None:
        super().__init__("AvatarLoaded", {"avatar": avatar_name, **extra})


class EnvironmentChanged(RenderEvent):
    def __init__(self, preset: str, **extra: Any) -> None:
        super().__init__("EnvironmentChanged", {"preset": preset, **extra})


class LightingChanged(RenderEvent):
    def __init__(self, preset: str, **extra: Any) -> None:
        super().__init__("LightingChanged", {"preset": preset, **extra})


class FrameStarted(RenderEvent):
    def __init__(self, frame_index: int = 0, **extra: Any) -> None:
        super().__init__("FrameStarted", {"frame_index": frame_index, **extra})


class FrameFinished(RenderEvent):
    def __init__(self, frame_index: int = 0, **extra: Any) -> None:
        super().__init__("FrameFinished", {"frame_index": frame_index, **extra})


class RenderEventBus:
    """Simple pub/sub bus — no hard callbacks between subsystems."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Listener]] = defaultdict(list)

    def subscribe(self, event_name: str, listener: Listener) -> None:
        self._listeners[event_name].append(listener)

    def unsubscribe(self, event_name: str, listener: Listener) -> None:
        if listener in self._listeners.get(event_name, []):
            self._listeners[event_name].remove(listener)

    def emit(
        self, event: RenderEvent | str, payload: dict[str, Any] | None = None
    ) -> None:
        if isinstance(event, str):
            event = RenderEvent(event, payload or {})
        for listener in list(self._listeners.get(event.name, [])):
            try:
                listener(event)
            except Exception:
                logger.warning(
                    "Event listener failed for %s", event.name, exc_info=True
                )


__all__ = [
    "RenderEvent",
    "AvatarLoaded",
    "EnvironmentChanged",
    "LightingChanged",
    "FrameStarted",
    "FrameFinished",
    "RenderEventBus",
]
