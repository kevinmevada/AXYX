"""Individual render-graph passes."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RenderContext:
    """Shared state for a single frame submission."""

    backend: Any
    plotter: Any = None
    extras: dict[str, Any] = field(default_factory=dict)


class RenderPass(ABC):
    """One step in the frame pipeline."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.enabled = True

    @abstractmethod
    def execute(self, context: RenderContext) -> None:
        """Run this pass."""


class CallbackPass(RenderPass):
    """Adapter that wraps a callable as a named pass."""

    def __init__(self, name: str, callback: Callable[[RenderContext], None]) -> None:
        super().__init__(name)
        self._callback = callback

    def execute(self, context: RenderContext) -> None:
        if not self.enabled:
            return
        self._callback(context)


__all__ = ["RenderContext", "RenderPass", "CallbackPass"]
