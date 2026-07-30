"""Retarget session — stateful multi-frame retargeting with filters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from motion_engine.rendering.avatar.pose.pose import AnimationPose
from motion_engine.rendering.avatar.retarget.filters import FilterConfig, TemporalFilter
from motion_engine.rendering.avatar.retarget.retarget_context import RetargetContext
from motion_engine.rendering.avatar.retarget.root_motion import RootMotionProcessor
from motion_engine.rendering.avatar.retarget.types import (
    FilterKind,
    MotionPose,
    RetargetStatistics,
    RootMotionMode,
)


@dataclass
class RetargetSession:
    """Owns context + temporal state across a motion sequence."""

    context: RetargetContext
    root_motion: RootMotionProcessor = field(
        default_factory=lambda: RootMotionProcessor(RootMotionMode.WORLD)
    )
    filter: TemporalFilter = field(
        default_factory=lambda: TemporalFilter(FilterConfig(kind=FilterKind.NONE))
    )
    frames_processed: int = 0
    last_pose: AnimationPose | None = None
    history: list[RetargetStatistics] = field(default_factory=list)

    def reset_filters(self) -> None:
        self.filter.reset()
        self.root_motion.reset()
        self.frames_processed = 0


__all__ = ["RetargetSession"]
