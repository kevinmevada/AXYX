"""Retarget session context — prepared mapping, offsets, scales."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.retarget.offset_solver import OffsetTable
from motion_engine.rendering.avatar.retarget.scale_mapper import ScaleFactors
from motion_engine.rendering.avatar.retarget.types import (
    BoneMapEntry,
    MappingProfile,
    MotionSkeleton,
    RetargetStatistics,
)
from motion_engine.rendering.avatar.skeleton.avatar_skeleton import AvatarSkeleton


@dataclass
class RetargetContext:
    """Immutable-enough prepared state for frame retargeting."""

    profile: MappingProfile
    source: MotionSkeleton
    target: AvatarSkeleton
    bind: BindPose
    active_entries: list[BoneMapEntry]
    offsets: OffsetTable
    scales: ScaleFactors
    missing_source: list[str] = field(default_factory=list)
    missing_target: list[str] = field(default_factory=list)
    target_names: set[str] = field(default_factory=set)
    stats: RetargetStatistics = field(default_factory=RetargetStatistics)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def coverage(self) -> float:
        return float(self.stats.coverage)


__all__ = ["RetargetContext"]
