"""Formal render lifecycle stages."""

from __future__ import annotations

import logging
from enum import Enum, auto
from typing import Any, Callable

logger = logging.getLogger(__name__)


class RenderPhase(Enum):
    """Ordered stages every renderer should follow."""

    UNINITIALIZED = auto()
    INITIALIZE = auto()
    LOAD_ASSETS = auto()
    CREATE_SCENE = auto()
    UPDATE = auto()
    ANIMATE = auto()
    RENDER = auto()
    PRESENT = auto()
    SHUTDOWN = auto()


_PHASE_ORDER = (
    RenderPhase.INITIALIZE,
    RenderPhase.LOAD_ASSETS,
    RenderPhase.CREATE_SCENE,
    RenderPhase.UPDATE,
    RenderPhase.ANIMATE,
    RenderPhase.RENDER,
    RenderPhase.PRESENT,
    RenderPhase.SHUTDOWN,
)


class RenderLifecycle:
    """Tracks and runs the formal Initialize → … → Shutdown pipeline.

    Subsystems register hooks per phase; missing hooks are no-ops.
    Errors in hooks are logged and do not abort the lifecycle (error recovery).
    """

    def __init__(self) -> None:
        self.phase = RenderPhase.UNINITIALIZED
        self._hooks: dict[RenderPhase, list[Callable[..., Any]]] = {
            p: [] for p in _PHASE_ORDER
        }

    def on(self, phase: RenderPhase, fn: Callable[..., Any]) -> None:
        """Register a hook for ``phase``."""
        self._hooks[phase].append(fn)

    def run_phase(self, phase: RenderPhase, *args: Any, **kwargs: Any) -> None:
        """Execute all hooks for ``phase`` and advance ``self.phase``."""
        self.phase = phase
        logger.debug("Lifecycle → %s", phase.name)
        for fn in self._hooks.get(phase, []):
            try:
                fn(*args, **kwargs)
            except Exception:
                logger.warning(
                    "Lifecycle hook failed in %s", phase.name, exc_info=True
                )

    def run_startup(self, *args: Any, **kwargs: Any) -> None:
        """Initialize → Load Assets → Create Scene."""
        for phase in (
            RenderPhase.INITIALIZE,
            RenderPhase.LOAD_ASSETS,
            RenderPhase.CREATE_SCENE,
        ):
            self.run_phase(phase, *args, **kwargs)

    def run_frame(self, *args: Any, **kwargs: Any) -> None:
        """Update → Animate → Render → Present."""
        for phase in (
            RenderPhase.UPDATE,
            RenderPhase.ANIMATE,
            RenderPhase.RENDER,
            RenderPhase.PRESENT,
        ):
            self.run_phase(phase, *args, **kwargs)

    def shutdown(self, *args: Any, **kwargs: Any) -> None:
        self.run_phase(RenderPhase.SHUTDOWN, *args, **kwargs)


__all__ = ["RenderPhase", "RenderLifecycle"]
