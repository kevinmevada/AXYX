"""Renderer state machine — explicit states for debugging and lifecycle."""

from __future__ import annotations

import logging
from enum import Enum

logger = logging.getLogger(__name__)


class RendererState(str, Enum):
    """Explicit renderer states (architecture freeze)."""

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    LOADING = "loading"
    RENDERING = "rendering"
    SHUTTING_DOWN = "shutting_down"
    DESTROYED = "destroyed"


# Allowed transitions: from → frozenset(to)
_TRANSITIONS: dict[RendererState, frozenset[RendererState]] = {
    RendererState.UNINITIALIZED: frozenset(
        {RendererState.INITIALIZING, RendererState.DESTROYED}
    ),
    RendererState.INITIALIZING: frozenset(
        {RendererState.READY, RendererState.SHUTTING_DOWN, RendererState.DESTROYED}
    ),
    RendererState.READY: frozenset(
        {
            RendererState.INITIALIZING,  # re-init / attach
            RendererState.LOADING,
            RendererState.RENDERING,
            RendererState.SHUTTING_DOWN,
            RendererState.DESTROYED,
        }
    ),
    RendererState.LOADING: frozenset(
        {RendererState.READY, RendererState.SHUTTING_DOWN, RendererState.DESTROYED}
    ),
    RendererState.RENDERING: frozenset(
        {RendererState.READY, RendererState.SHUTTING_DOWN, RendererState.DESTROYED}
    ),
    RendererState.SHUTTING_DOWN: frozenset({RendererState.DESTROYED}),
    RendererState.DESTROYED: frozenset(),
}


class RendererStateMachine:
    """Tracks renderer state with validated transitions."""

    def __init__(self, initial: RendererState = RendererState.UNINITIALIZED) -> None:
        self._state = initial

    @property
    def state(self) -> RendererState:
        return self._state

    def can_transition(self, new_state: RendererState) -> bool:
        return new_state in _TRANSITIONS.get(self._state, frozenset())

    def transition(self, new_state: RendererState, *, force: bool = False) -> bool:
        """Move to ``new_state``. Returns True on success.

        Invalid transitions log a warning and return False unless ``force``.
        """
        if new_state == self._state:
            return True
        if not force and not self.can_transition(new_state):
            logger.warning(
                "Invalid renderer state transition %s → %s",
                self._state.value,
                new_state.value,
            )
            return False
        logger.debug("Renderer state %s → %s", self._state.value, new_state.value)
        self._state = new_state
        return True

    def __repr__(self) -> str:
        return f"RendererStateMachine({self._state.value})"


__all__ = ["RendererState", "RendererStateMachine"]
