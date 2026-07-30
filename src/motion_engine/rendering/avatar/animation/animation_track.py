"""Per-bone animation track."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np

from motion_engine.rendering.avatar.animation.exceptions import AnimationValidationError
from motion_engine.rendering.avatar.animation.interpolation import (
    catmull_rom_tangent,
    find_key_bracket,
    interpolate_quat,
    interpolate_vec,
)
from motion_engine.rendering.avatar.animation.keyframe import Keyframe
from motion_engine.rendering.avatar.animation.quaternion import quat_identity
from motion_engine.rendering.avatar.animation.types import (
    InterpolationMode,
    Quat,
    TrackChannel,
    Vec3,
)


@dataclass(frozen=True, slots=True)
class SampledTRS:
    """Sparse TRS sample produced by a track."""

    translation: Vec3 | None = None
    rotation_xyzw: Quat | None = None
    scale: Vec3 | None = None


@dataclass(frozen=True, slots=True)
class AnimationTrack:
    """One track targeting a single bone (sparse channels allowed)."""

    bone_name: str
    channel: TrackChannel
    keyframes: tuple[Keyframe, ...]
    interpolation: InterpolationMode = InterpolationMode.LINEAR
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        keys = tuple(sorted(self.keyframes, key=lambda k: k.time))
        object.__setattr__(self, "keyframes", keys)
        object.__setattr__(self, "bone_name", str(self.bone_name))
        object.__setattr__(self, "metadata", dict(self.metadata))
        if not keys:
            raise AnimationValidationError(
                f"Track {self.bone_name!r} has no keyframes",
                code="ANIM_TRACK_EMPTY",
            )
        times = [k.time for k in keys]
        if any(times[i] > times[i + 1] for i in range(len(times) - 1)):
            raise AnimationValidationError(
                f"Track {self.bone_name!r} keyframes not sorted",
                code="ANIM_TRACK_ORDER",
            )

    @property
    def keyframe_count(self) -> int:
        return len(self.keyframes)

    @property
    def start_time(self) -> float:
        return float(self.keyframes[0].time)

    @property
    def end_time(self) -> float:
        return float(self.keyframes[-1].time)

    @property
    def duration(self) -> float:
        return max(0.0, self.end_time - self.start_time)

    def times(self) -> tuple[float, ...]:
        return tuple(k.time for k in self.keyframes)

    def sample(self, time: float) -> SampledTRS:
        """Sample this track at ``time`` (seconds)."""
        keys = self.keyframes
        times = [k.time for k in keys]
        i0, i1, t = find_key_bracket(times, float(time))
        a, b = keys[i0], keys[i1]
        mode = self.interpolation

        translation = None
        rotation = None
        scale = None

        if self.channel in (TrackChannel.TRANSLATION, TrackChannel.TRANSFORM):
            if a.translation is not None and b.translation is not None:
                ta, tb = a.translation, b.translation
                tan_a = tan_b = None
                if mode is InterpolationMode.CUBIC and len(keys) >= 2:
                    prev = keys[max(0, i0 - 1)].translation or ta
                    nxt = keys[min(len(keys) - 1, i1 + 1)].translation or tb
                    tan_a = catmull_rom_tangent(prev, tb)
                    tan_b = catmull_rom_tangent(ta, nxt)
                translation = interpolate_vec(ta, tb, t, mode, tangent_a=tan_a, tangent_b=tan_b)
            elif a.translation is not None:
                translation = np.asarray(a.translation, dtype=np.float64)

        if self.channel in (TrackChannel.ROTATION, TrackChannel.TRANSFORM):
            qa = a.rotation_xyzw
            qb = b.rotation_xyzw
            if qa is not None and qb is not None:
                rotation = interpolate_quat(qa, qb, t, mode)
            elif qa is not None:
                rotation = np.asarray(qa, dtype=np.float64)
            elif qb is not None:
                rotation = np.asarray(qb, dtype=np.float64)

        if self.channel in (TrackChannel.SCALE, TrackChannel.TRANSFORM):
            if a.scale is not None and b.scale is not None:
                tan_a = tan_b = None
                if mode is InterpolationMode.CUBIC and len(keys) >= 2:
                    prev = keys[max(0, i0 - 1)].scale or a.scale
                    nxt = keys[min(len(keys) - 1, i1 + 1)].scale or b.scale
                    tan_a = catmull_rom_tangent(prev, b.scale)
                    tan_b = catmull_rom_tangent(a.scale, nxt)
                scale = interpolate_vec(a.scale, b.scale, t, mode, tangent_a=tan_a, tangent_b=tan_b)
            elif a.scale is not None:
                scale = np.asarray(a.scale, dtype=np.float64)

        return SampledTRS(translation=translation, rotation_xyzw=rotation, scale=scale)


def default_rotation() -> Quat:
    return quat_identity()


__all__ = ["AnimationTrack", "SampledTRS", "default_rotation"]
