"""Joint-level mapping (aliases, one-to-many expansion)."""

from __future__ import annotations

from motion_engine.rendering.avatar.retarget.bone_mapping import BoneMapping
from motion_engine.rendering.avatar.retarget.types import BoneMapEntry, MappingKind, MappingProfile


class JointMapping:
    """High-level joint name resolution with alias support."""

    def __init__(
        self,
        profile: MappingProfile,
        *,
        aliases: dict[str, str] | None = None,
    ) -> None:
        self.profile = profile
        self.aliases = dict(aliases or {})
        self.bones = BoneMapping(profile)

    def canonicalize(self, name: str) -> str:
        return self.aliases.get(name, name)

    def map_name(self, source: str) -> list[str]:
        src = self.canonicalize(source)
        entry = self.bones.get(src)
        if entry is None:
            return []
        return list(entry.targets)

    def primary(self, source: str) -> str | None:
        targets = self.map_name(source)
        return targets[0] if targets else None

    def expand_one_to_many(self, source: str, value_weight: float = 1.0) -> list[tuple[str, float]]:
        entry = self.bones.get(self.canonicalize(source))
        if entry is None:
            return []
        n = len(entry.targets)
        if entry.kind == MappingKind.ONE_TO_MANY and n > 1:
            w = value_weight / n
            return [(t, w) for t in entry.targets]
        return [(t, entry.weight * value_weight) for t in entry.targets]

    def invert_many_to_one(self) -> dict[str, list[str]]:
        return self.profile.target_to_sources()

    def entries(self) -> list[BoneMapEntry]:
        return list(self.profile.bones)


__all__ = ["JointMapping"]
