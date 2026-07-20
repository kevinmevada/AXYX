"""MetaHuman mapping facade over YAML retarget profiles."""

from __future__ import annotations

from pathlib import Path

from motion_engine.animation_clip import AnimationClip
from motion_engine.retarget import (
    DEFAULT_METAHUMAN_MAPPING,
    MetaHumanRetargeter,
    RetargetProfile,
)


class MetaHumanMapper:
    """Load and apply MetaHuman joint mappings without hardcoded names."""

    def __init__(self, mapping_path: str | Path | None = None) -> None:
        path = Path(mapping_path) if mapping_path else DEFAULT_METAHUMAN_MAPPING
        self.profile = RetargetProfile.from_yaml(path)
        self._retargeter = MetaHumanRetargeter(path)

    @property
    def joint_map(self) -> dict[str, str]:
        return dict(self.profile.joint_map)

    def map_joint(self, source_name: str) -> str | None:
        return self.profile.joint_map.get(source_name)

    def apply(self, clip: AnimationClip) -> AnimationClip:
        """Retarget a Motion Engine clip onto MetaHuman joint names."""
        return self._retargeter.retarget(clip)
