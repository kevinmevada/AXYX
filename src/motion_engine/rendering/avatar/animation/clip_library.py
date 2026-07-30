"""Clip library — named registry of animation clips."""

from __future__ import annotations

from dataclasses import dataclass, field

from motion_engine.rendering.avatar.animation.animation_clip import AnimationClip
from motion_engine.rendering.avatar.animation.exceptions import AnimationFactoryError


@dataclass
class ClipLibrary:
    """In-memory clip registry (Mixamo / mocap / research packs)."""

    clips: dict[str, AnimationClip] = field(default_factory=dict)

    def add(self, clip: AnimationClip, *, alias: str | None = None) -> None:
        key = alias or clip.name
        self.clips[key] = clip

    def get(self, name: str) -> AnimationClip:
        if name not in self.clips:
            raise AnimationFactoryError(
                f"Clip {name!r} not in library",
                code="ANIM_LIB_MISSING",
            )
        return self.clips[name]

    def try_get(self, name: str) -> AnimationClip | None:
        return self.clips.get(name)

    def names(self) -> list[str]:
        return sorted(self.clips.keys())

    def __len__(self) -> int:
        return len(self.clips)


__all__ = ["ClipLibrary"]
