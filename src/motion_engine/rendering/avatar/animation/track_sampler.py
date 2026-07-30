"""Track sampler — sample all tracks of a clip at a time."""

from __future__ import annotations

from dataclasses import dataclass

from motion_engine.rendering.avatar.animation.animation_clip import AnimationClip
from motion_engine.rendering.avatar.animation.animation_track import SampledTRS


@dataclass(frozen=True, slots=True)
class BoneSample:
    bone_name: str
    translation: object | None
    rotation_xyzw: object | None
    scale: object | None


@dataclass(frozen=True, slots=True)
class ClipSample:
    """Sparse per-bone TRS at a single time."""

    time: float
    bones: dict[str, SampledTRS]


class TrackSampler:
    """Sample every track in a clip and merge channels per bone."""

    def sample(self, clip: AnimationClip, time: float) -> ClipSample:
        merged: dict[str, SampledTRS] = {}
        for track in clip.tracks:
            s = track.sample(time)
            prev = merged.get(track.bone_name)
            if prev is None:
                merged[track.bone_name] = s
                continue
            merged[track.bone_name] = SampledTRS(
                translation=s.translation if s.translation is not None else prev.translation,
                rotation_xyzw=s.rotation_xyzw if s.rotation_xyzw is not None else prev.rotation_xyzw,
                scale=s.scale if s.scale is not None else prev.scale,
            )
        return ClipSample(time=float(time), bones=merged)


__all__ = ["TrackSampler", "ClipSample", "BoneSample"]
