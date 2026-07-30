"""Runtime types — session selections, pipeline frames, presets."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.floating[Any]]


class RuntimePhase(str, Enum):
    UNINITIALIZED = "uninitialized"
    READY = "ready"
    PREPARED = "prepared"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"
    SHUTDOWN = "shutdown"
    ERROR = "error"


class AvatarKind(str, Enum):
    FIXTURE = "fixture"
    ARMY_GIRL = "army_girl"
    METAHUMAN = "metahuman"
    CUSTOM = "custom"


class PlaybackMode(str, Enum):
    RETARGET = "retarget"  # clinical / synthetic gait → retarget → skin
    ANIMATION = "animation"  # M5 procedural clips
    BIND = "bind"  # static bind pose


@dataclass(frozen=True, slots=True)
class PipelineFrame:
    """One fully processed research frame."""

    index: int
    time: float
    pose_name: str
    vertex_count: int
    bone_count: int
    finite: bool
    stages_ns: Mapping[str, int] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "stages_ns", dict(self.stages_ns))
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass
class RuntimeReport:
    """Aggregated runtime statistics snapshot."""

    fps: float = 0.0
    frame_time_ms: float = 0.0
    frames: int = 0
    retarget_ms: float = 0.0
    skinning_ms: float = 0.0
    animation_ms: float = 0.0
    pipeline_ms: float = 0.0
    memory_mb: float = 0.0
    phase: str = RuntimePhase.UNINITIALIZED.value
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "fps": self.fps,
            "frame_time_ms": self.frame_time_ms,
            "frames": self.frames,
            "retarget_ms": self.retarget_ms,
            "skinning_ms": self.skinning_ms,
            "animation_ms": self.animation_ms,
            "pipeline_ms": self.pipeline_ms,
            "memory_mb": self.memory_mb,
            "phase": self.phase,
            **self.extra,
        }


__all__ = [
    "FloatArray",
    "RuntimePhase",
    "AvatarKind",
    "PlaybackMode",
    "PipelineFrame",
    "RuntimeReport",
]
