"""Avatar joint remapping hooks (Phase-1 Digital Twin prep — stubs)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Mapping

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AvatarRetargetProfile:
    """Source → target joint name map for future skinned avatars."""

    joint_map: dict[str, str] = field(default_factory=dict)
    root_joint: str | None = None


class AvatarRetarget:
    """Lightweight remapper — does not replace ``motion_engine.retarget``."""

    def __init__(self, profile: AvatarRetargetProfile | None = None) -> None:
        self.profile = profile or AvatarRetargetProfile()

    def map_joint(self, source_name: str) -> str:
        """Map a source joint name; identity if unmapped."""
        return self.profile.joint_map.get(source_name, source_name)

    def apply_names(self, names: Mapping[str, object]) -> dict[str, object]:
        """Rename keys in a joint dictionary."""
        return {self.map_joint(k): v for k, v in names.items()}


__all__ = ["AvatarRetargetProfile", "AvatarRetarget"]
