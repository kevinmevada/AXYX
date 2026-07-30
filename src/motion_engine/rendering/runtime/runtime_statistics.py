"""Runtime statistics aggregation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from motion_engine.rendering.runtime.types import PipelineFrame, RuntimeReport


@dataclass
class RuntimeStatistics:
    """Accumulate per-frame pipeline metrics."""

    frames: list[PipelineFrame] = field(default_factory=list)

    def add(self, frame: PipelineFrame) -> None:
        self.frames.append(frame)

    def clear(self) -> None:
        self.frames.clear()

    def report(self, *, memory_mb: float = 0.0, phase: str = "") -> RuntimeReport:
        if not self.frames:
            return RuntimeReport(memory_mb=memory_mb, phase=phase)
        total_ns = []
        retarget_ns = []
        skin_ns = []
        anim_ns = []
        for fr in self.frames:
            stages = fr.stages_ns
            total_ns.append(int(stages.get("frame", sum(stages.values()))))
            retarget_ns.append(int(stages.get("retarget", 0)))
            skin_ns.append(int(stages.get("skinning", 0)))
            anim_ns.append(int(stages.get("animation", 0)))
        mean_frame = float(np.mean(total_ns))
        fps = 1e9 / mean_frame if mean_frame > 0 else 0.0
        return RuntimeReport(
            fps=fps,
            frame_time_ms=mean_frame / 1e6,
            frames=len(self.frames),
            retarget_ms=float(np.mean(retarget_ns)) / 1e6 if retarget_ns else 0.0,
            skinning_ms=float(np.mean(skin_ns)) / 1e6 if skin_ns else 0.0,
            animation_ms=float(np.mean(anim_ns)) / 1e6 if anim_ns else 0.0,
            pipeline_ms=mean_frame / 1e6,
            memory_mb=memory_mb,
            phase=phase,
            extra={
                "finite_frames": sum(1 for f in self.frames if f.finite),
                "last_index": self.frames[-1].index,
            },
        )

    def as_dict(self) -> dict[str, Any]:
        return self.report().as_dict()


__all__ = ["RuntimeStatistics"]
