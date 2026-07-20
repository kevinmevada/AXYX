"""Standardized per-frame performance metrics.

Always present — unused fields stay at zero / placeholder defaults so
dashboards and benchmarks never need optional-key checks.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class PerformanceMetrics:
    """Canonical frame metrics object (architecture freeze)."""

    # Timing (milliseconds)
    frame_ms: float = 0.0
    update_ms: float = 0.0
    animation_ms: float = 0.0
    skinning_ms: float = 0.0
    render_ms: float = 0.0

    # Throughput
    fps: float = 0.0
    draw_calls: int = 0
    vertices: int = 0
    triangles: int = 0

    # Memory / upload
    gpu_upload_bytes: int = 0
    memory_bytes: int = 0

    # Extensible placeholders for future backends
    extras: dict[str, Any] = field(default_factory=dict)

    def reset_counters(self) -> None:
        """Clear per-frame counters (keep memory_bytes)."""
        self.frame_ms = 0.0
        self.update_ms = 0.0
        self.animation_ms = 0.0
        self.skinning_ms = 0.0
        self.render_ms = 0.0
        self.fps = 0.0
        self.draw_calls = 0
        self.vertices = 0
        self.triangles = 0
        self.gpu_upload_bytes = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def apply_frame_time(self, elapsed_s: float) -> None:
        """Set ``frame_ms`` / ``fps`` from a wall-clock elapsed seconds value."""
        elapsed_s = max(float(elapsed_s), 1e-9)
        self.frame_ms = elapsed_s * 1000.0
        self.fps = 1.0 / elapsed_s


# Backward-compatible alias used by FrameContext / profiler.
FrameStatistics = PerformanceMetrics


__all__ = ["PerformanceMetrics", "FrameStatistics"]
