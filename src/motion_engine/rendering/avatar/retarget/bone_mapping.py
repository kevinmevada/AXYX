"""Bone-level mapping helpers."""

from __future__ import annotations

from motion_engine.rendering.avatar.retarget.exceptions import MappingError
from motion_engine.rendering.avatar.retarget.types import (
    BoneMapEntry,
    MappingKind,
    MappingProfile,
    MotionSkeleton,
)


class BoneMapping:
    """Resolve bone map entries against source/target name sets."""

    def __init__(self, profile: MappingProfile) -> None:
        self.profile = profile
        self._by_source = {e.source: e for e in profile.bones}

    def get(self, source: str) -> BoneMapEntry | None:
        return self._by_source.get(source)

    def resolve(
        self,
        source_names: set[str],
        target_names: set[str],
        *,
        strict: bool = False,
    ) -> tuple[list[BoneMapEntry], list[str], list[str]]:
        """Return (active_entries, missing_source, missing_target)."""
        active: list[BoneMapEntry] = []
        missing_src: list[str] = []
        missing_tgt: list[str] = []

        for entry in self.profile.bones:
            if entry.source in self.profile.ignore_source:
                continue
            if entry.source not in source_names:
                if entry.optional or entry.kind == MappingKind.OPTIONAL:
                    continue
                missing_src.append(entry.source)
                if strict and not entry.optional:
                    raise MappingError(f"Missing source bone: {entry.source}")
                continue
            valid_targets = [t for t in entry.targets if t in target_names and t not in self.profile.ignore_target]
            if not valid_targets:
                missing_tgt.extend(list(entry.targets))
                if entry.optional:
                    continue
                if strict:
                    raise MappingError(f"Missing target bone(s) for {entry.source}: {entry.targets}")
                continue
            if len(valid_targets) != len(entry.targets):
                entry = BoneMapEntry(
                    source=entry.source,
                    targets=tuple(valid_targets),
                    kind=entry.kind,
                    weight=entry.weight,
                    optional=entry.optional,
                    pre_rotation_xyzw=entry.pre_rotation_xyzw,
                    post_rotation_xyzw=entry.post_rotation_xyzw,
                    copy_translation=entry.copy_translation,
                    metadata=entry.metadata,
                )
            active.append(entry)

        return active, missing_src, missing_tgt

    def coverage(self, source: MotionSkeleton, target_names: set[str]) -> float:
        src = set(source.joint_names) - set(self.profile.ignore_source)
        if not src:
            return 0.0
        mapped = 0
        for name in src:
            e = self.get(name)
            if e and any(t in target_names for t in e.targets):
                mapped += 1
        return mapped / len(src)


__all__ = ["BoneMapping"]
