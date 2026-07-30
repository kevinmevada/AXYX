"""Animation clip — collection of tracks, markers, and events."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from motion_engine.rendering.avatar.animation.animation_track import AnimationTrack
from motion_engine.rendering.avatar.animation.constants import DEFAULT_FPS
from motion_engine.rendering.avatar.animation.events import AnimationEvent
from motion_engine.rendering.avatar.animation.exceptions import AnimationValidationError
from motion_engine.rendering.avatar.animation.markers import AnimationMarker


@dataclass(frozen=True, slots=True)
class AnimationClip:
    """Immutable authored animation asset."""

    name: str
    duration: float
    tracks: tuple[AnimationTrack, ...]
    markers: tuple[AnimationMarker, ...] = ()
    events: tuple[AnimationEvent, ...] = ()
    fps: float = DEFAULT_FPS
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(self, "duration", max(0.0, float(self.duration)))
        object.__setattr__(self, "tracks", tuple(self.tracks))
        object.__setattr__(self, "markers", tuple(sorted(self.markers, key=lambda m: m.time)))
        object.__setattr__(self, "events", tuple(sorted(self.events, key=lambda e: e.time)))
        object.__setattr__(self, "fps", float(self.fps) if self.fps > 0 else DEFAULT_FPS)
        object.__setattr__(self, "metadata", dict(self.metadata))
        # Duration must cover all tracks.
        if self.tracks:
            end = max(t.end_time for t in self.tracks)
            if self.duration + 1e-9 < end:
                object.__setattr__(self, "duration", float(end))

    @property
    def track_count(self) -> int:
        return len(self.tracks)

    @property
    def bone_names(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(t.bone_name for t in self.tracks))

    @property
    def bone_count(self) -> int:
        return len(self.bone_names)

    @property
    def frame_count(self) -> int:
        if self.duration <= 0.0:
            return 1
        return max(1, int(round(self.duration * self.fps)) + 1)

    def tracks_for(self, bone_name: str) -> tuple[AnimationTrack, ...]:
        return tuple(t for t in self.tracks if t.bone_name == bone_name)

    def marker(self, name: str) -> AnimationMarker | None:
        for m in self.markers:
            if m.name == name:
                return m
        return None

    def validate(self) -> None:
        if not self.tracks:
            raise AnimationValidationError(
                f"Clip {self.name!r} has no tracks",
                code="ANIM_CLIP_EMPTY",
            )
        for t in self.tracks:
            if t.keyframe_count == 0:
                raise AnimationValidationError(
                    f"Empty track on {t.bone_name!r}",
                    code="ANIM_CLIP_TRACK",
                )


__all__ = ["AnimationClip"]
