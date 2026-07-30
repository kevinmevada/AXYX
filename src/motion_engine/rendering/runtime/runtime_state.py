"""Runtime state machine."""

from __future__ import annotations

from motion_engine.rendering.runtime.exceptions import RuntimeStateError
from motion_engine.rendering.runtime.types import RuntimePhase

_ALLOWED: dict[RuntimePhase, set[RuntimePhase]] = {
    RuntimePhase.UNINITIALIZED: {RuntimePhase.READY, RuntimePhase.ERROR, RuntimePhase.SHUTDOWN},
    RuntimePhase.READY: {
        RuntimePhase.PREPARED,
        RuntimePhase.STOPPED,
        RuntimePhase.ERROR,
        RuntimePhase.SHUTDOWN,
    },
    RuntimePhase.PREPARED: {
        RuntimePhase.PLAYING,
        RuntimePhase.PAUSED,
        RuntimePhase.STOPPED,
        RuntimePhase.READY,
        RuntimePhase.ERROR,
        RuntimePhase.SHUTDOWN,
    },
    RuntimePhase.PLAYING: {
        RuntimePhase.PAUSED,
        RuntimePhase.STOPPED,
        RuntimePhase.PREPARED,
        RuntimePhase.ERROR,
        RuntimePhase.SHUTDOWN,
    },
    RuntimePhase.PAUSED: {
        RuntimePhase.PLAYING,
        RuntimePhase.STOPPED,
        RuntimePhase.PREPARED,
        RuntimePhase.ERROR,
        RuntimePhase.SHUTDOWN,
    },
    RuntimePhase.STOPPED: {
        RuntimePhase.READY,
        RuntimePhase.PREPARED,
        RuntimePhase.PLAYING,
        RuntimePhase.SHUTDOWN,
        RuntimePhase.ERROR,
    },
    RuntimePhase.ERROR: {RuntimePhase.READY, RuntimePhase.SHUTDOWN, RuntimePhase.STOPPED},
    RuntimePhase.SHUTDOWN: set(),
}


class RuntimeState:
    """Tracks lifecycle phase with validated transitions."""

    def __init__(self) -> None:
        self.phase = RuntimePhase.UNINITIALIZED
        self.last_error: str | None = None

    def transition(self, target: RuntimePhase, *, force: bool = False) -> None:
        if not force and target not in _ALLOWED.get(self.phase, set()):
            raise RuntimeStateError(
                f"Illegal transition {self.phase.value} -> {target.value}"
            )
        self.phase = target
        if target != RuntimePhase.ERROR:
            self.last_error = None

    def fail(self, message: str) -> None:
        self.last_error = message
        self.phase = RuntimePhase.ERROR


__all__ = ["RuntimeState"]
