"""Per-frame and session rendering contexts."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from motion_engine.rendering.metrics import FrameStatistics, PerformanceMetrics

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RenderFlags:
    """Boolean render toggles for the current frame."""

    show_ground: bool = True
    show_grid: bool = True
    show_axes: bool = False
    show_shadows: bool = True
    show_overlays: bool = True
    wireframe: bool = False


@dataclass(slots=True)
class FrameContext:
    """Single-frame payload passed to every render pass.

    Replaces ad-hoc parameter lists. Passes should read from this object
    instead of reaching into unrelated subsystems.
    """

    delta_time: float = 0.0
    viewport_width: int = 0
    viewport_height: int = 0
    camera: Any | None = None
    active_avatar: Any | None = None
    active_scene: Any | None = None
    quality: Any | None = None
    settings: Any | None = None
    flags: RenderFlags = field(default_factory=RenderFlags)
    statistics: FrameStatistics = field(default_factory=FrameStatistics)
    extras: dict[str, Any] = field(default_factory=dict)

    @property
    def viewport_size(self) -> tuple[int, int]:
        """``(width, height)`` in pixels."""
        return (self.viewport_width, self.viewport_height)

    @property
    def metrics(self) -> PerformanceMetrics:
        """Alias for :attr:`statistics` (canonical metrics object)."""
        return self.statistics


@dataclass(slots=True)
class RenderingContext:
    """Session-long rendering state (survives across frames)."""

    backend: Any | None = None
    resource_manager: Any | None = None
    scene_graph: Any | None = None
    avatar_manager: Any | None = None
    lighting_manager: Any | None = None
    environment: Any | None = None
    event_bus: Any | None = None
    settings: Any | None = None
    quality_name: str = "high"
    lighting_preset: str = "studio"
    environment_preset: str = "studio"
    camera_preset: str = "clinical"

    def make_frame(
        self,
        *,
        delta_time: float = 0.0,
        viewport_width: int = 0,
        viewport_height: int = 0,
        camera: Any | None = None,
        flags: RenderFlags | None = None,
    ) -> FrameContext:
        """Build a :class:`FrameContext` from session state."""
        avatar = None
        if self.avatar_manager is not None:
            try:
                avatar = self.avatar_manager.get_active()
            except Exception:
                logger.debug("Active avatar lookup failed", exc_info=True)
        return FrameContext(
            delta_time=delta_time,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            camera=camera,
            active_avatar=avatar,
            active_scene=self.scene_graph,
            quality=self.quality_name,
            settings=self.settings,
            flags=flags or RenderFlags(),
        )


__all__ = [
    "RenderFlags",
    "FrameStatistics",
    "PerformanceMetrics",
    "FrameContext",
    "RenderingContext",
]
