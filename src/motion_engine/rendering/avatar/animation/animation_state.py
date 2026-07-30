"""Animation state descriptors for the controller."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from motion_engine.rendering.avatar.animation.animation_clip import AnimationClip
from motion_engine.rendering.avatar.animation.types import ControllerState, LoopMode


@dataclass
class AnimationState:
    """Named controller state bound to a clip."""

    name: str
    kind: ControllerState
    clip: AnimationClip
    loop_mode: LoopMode = LoopMode.LOOP
    speed: float = 1.0
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class Transition:
    """Crossfade transition between controller states."""

    source: str
    target: str
    duration: float = 0.25
    metadata: Mapping[str, Any] = field(default_factory=dict)


__all__ = ["AnimationState", "Transition"]
