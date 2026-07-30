"""High-level sampler facade."""

from __future__ import annotations

from motion_engine.rendering.avatar.animation.animation_clip import AnimationClip
from motion_engine.rendering.avatar.animation.track_sampler import ClipSample, TrackSampler


class Sampler:
    """Convenience sampler for clips."""

    def __init__(self) -> None:
        self._tracks = TrackSampler()

    def sample_clip(self, clip: AnimationClip, time: float) -> ClipSample:
        return self._tracks.sample(clip, time)


__all__ = ["Sampler"]
