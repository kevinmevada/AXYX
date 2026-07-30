"""Runtime event bus."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable

Listener = Callable[["RuntimeEvent"], None]


@dataclass(frozen=True, slots=True)
class RuntimeEvent:
    name: str
    payload: dict[str, Any] = field(default_factory=dict)


class RuntimeEventBus:
    """Simple synchronous pub/sub for research instrumentation."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Listener]] = defaultdict(list)
        self.history: list[RuntimeEvent] = []

    def on(self, name: str, listener: Listener) -> None:
        self._listeners[name].append(listener)

    def off(self, name: str, listener: Listener) -> None:
        if name in self._listeners:
            self._listeners[name] = [x for x in self._listeners[name] if x is not listener]

    def emit(self, name: str, **payload: Any) -> RuntimeEvent:
        ev = RuntimeEvent(name=name, payload=dict(payload))
        self.history.append(ev)
        for listener in list(self._listeners.get(name, [])):
            listener(ev)
        for listener in list(self._listeners.get("*", [])):
            listener(ev)
        return ev

    def clear(self) -> None:
        self._listeners.clear()
        self.history.clear()


__all__ = ["RuntimeEvent", "RuntimeEventBus"]
