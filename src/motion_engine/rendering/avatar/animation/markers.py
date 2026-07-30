"""Named markers on an animation clip."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class AnimationMarker:
    """Named time marker (LoopStart, FootContact, research events, …)."""

    name: str
    time: float
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(self, "time", float(self.time))
        object.__setattr__(self, "metadata", dict(self.metadata))


__all__ = ["AnimationMarker"]
