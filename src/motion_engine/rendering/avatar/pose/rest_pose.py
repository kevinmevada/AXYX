"""Rest-pose kind tagging (T-pose / A-pose / imported / custom)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from motion_engine.rendering.avatar.pose.types import RestPoseKind


@dataclass(frozen=True, slots=True)
class RestPoseInfo:
    """Declares which rest style a bind pose represents.

    Architecture stays identical across kinds; only metadata differs so future
    T-pose / A-pose authoring can share the same BindPose runtime.
    """

    kind: RestPoseKind = RestPoseKind.IMPORTED
    label: str = ""
    notes: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra", dict(self.extra))
        if not self.label:
            object.__setattr__(self, "label", self.kind.value)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "label": self.label,
            "notes": self.notes,
            "extra": dict(self.extra),
        }


__all__ = ["RestPoseInfo", "RestPoseKind"]
