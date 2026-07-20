"""Ordered render graph — Environment → Lighting → Avatar → Effects → Overlay → Present."""

from __future__ import annotations

import logging
from typing import Iterable

from motion_engine.rendering.rendergraph.render_pass import (
    CallbackPass,
    RenderContext,
    RenderPass,
)

logger = logging.getLogger(__name__)

DEFAULT_PASS_ORDER: tuple[str, ...] = (
    "environment",
    "lighting",
    "avatar",
    "effects",
    "overlay",
    "present",
)


class RenderGraph:
    """Sequential frame pipeline with named extension points.

    Implementation is intentionally simple (ordered list). Future work can
    add resource barriers / async compute without changing pass authors.
    """

    def __init__(self, passes: Iterable[RenderPass] | None = None) -> None:
        self._passes: list[RenderPass] = list(passes or [])

    def add_pass(self, render_pass: RenderPass) -> None:
        """Append a pass (or replace same-name pass)."""
        self._passes = [p for p in self._passes if p.name != render_pass.name]
        self._passes.append(render_pass)

    def add_callback(self, name: str, callback) -> None:
        """Register a callable under ``name``."""
        self.add_pass(CallbackPass(name, callback))

    def get_pass(self, name: str) -> RenderPass | None:
        """Lookup a pass by name."""
        for item in self._passes:
            if item.name == name:
                return item
        return None

    def execute(self, context: RenderContext) -> None:
        """Run all enabled passes in registration order."""
        for item in self._passes:
            if not item.enabled:
                continue
            try:
                item.execute(context)
            except Exception:
                logger.exception("Render pass %r failed", item.name)
                raise

    @classmethod
    def create_default(cls) -> RenderGraph:
        """Empty graph with reserved pass names for documentation / wiring."""
        graph = cls()
        for name in DEFAULT_PASS_ORDER:
            graph.add_callback(name, lambda _ctx, _n=name: None)
        return graph


__all__ = ["RenderGraph", "DEFAULT_PASS_ORDER"]
