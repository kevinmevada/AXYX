"""Animation statistics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from motion_engine.rendering.avatar.animation.animation_clip import AnimationClip


@dataclass(frozen=True, slots=True)
class AnimationStatistics:
    clip_name: str
    duration: float
    frame_count: int
    track_count: int
    bone_count: int
    marker_count: int
    event_count: int
    fps: float
    evaluation_ns: int = 0
    sampling_ns: int = 0
    interpolation_keys: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_clip_statistics(
    clip: AnimationClip,
    *,
    evaluation_ns: int = 0,
    sampling_ns: int = 0,
) -> AnimationStatistics:
    keys = sum(t.keyframe_count for t in clip.tracks)
    return AnimationStatistics(
        clip_name=clip.name,
        duration=clip.duration,
        frame_count=clip.frame_count,
        track_count=clip.track_count,
        bone_count=clip.bone_count,
        marker_count=len(clip.markers),
        event_count=len(clip.events),
        fps=clip.fps,
        evaluation_ns=int(evaluation_ns),
        sampling_ns=int(sampling_ns),
        interpolation_keys=keys,
    )


__all__ = ["AnimationStatistics", "compute_clip_statistics"]
