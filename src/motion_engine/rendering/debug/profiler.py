"""Simple CPU-side render profiler."""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator

from motion_engine.rendering.metrics import PerformanceMetrics

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RenderProfiler:
    """Accumulates timing / counters for diagnostics overlays."""

    stats: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    _frame_t0: float = 0.0

    @property
    def metrics(self) -> PerformanceMetrics:
        return self.stats

    def begin_frame(self) -> None:
        self._frame_t0 = time.perf_counter()
        self.stats.reset_counters()

    def end_frame(self) -> PerformanceMetrics:
        elapsed = max(time.perf_counter() - self._frame_t0, 1e-9)
        self.stats.apply_frame_time(elapsed)
        self.stats.render_ms = self.stats.frame_ms
        return self.stats

    def add_draw(self, *, vertices: int = 0, triangles: int = 0) -> None:
        self.stats.draw_calls += 1
        self.stats.vertices += vertices
        self.stats.triangles += triangles

    @contextmanager
    def measure(self, label: str) -> Iterator[None]:
        t0 = time.perf_counter()
        try:
            yield
        finally:
            dt = (time.perf_counter() - t0) * 1000.0
            logger.debug("profile %s: %.3f ms", label, dt)
            if label == "animation":
                self.stats.animation_ms = dt
            elif label == "update":
                self.stats.update_ms = dt
            elif label == "skinning":
                self.stats.skinning_ms = dt
            elif label == "render":
                self.stats.render_ms = dt


__all__ = ["RenderProfiler"]
