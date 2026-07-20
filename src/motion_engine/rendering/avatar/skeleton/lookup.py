"""O(1) bone lookup tables for AvatarSkeleton."""

from __future__ import annotations

from dataclasses import dataclass

from motion_engine.rendering.avatar.skeleton.bone import Bone
from motion_engine.rendering.avatar.skeleton.exceptions import BoneNotFoundError


@dataclass(frozen=True, slots=True)
class BoneLookup:
    """Name and index lookup with O(1) access."""

    by_name: dict[str, int]
    by_id: dict[int, int]
    bones: tuple[Bone, ...]

    @classmethod
    def build(cls, bones: tuple[Bone, ...]) -> BoneLookup:
        """Construct lookup tables from bones."""
        by_name: dict[str, int] = {}
        by_id: dict[int, int] = {}
        for b in bones:
            by_name[b.name] = b.index
            by_id[int(b.id)] = b.index
        return cls(by_name=by_name, by_id=by_id, bones=bones)

    def exists(self, key: str | int) -> bool:
        """Return True if ``key`` (name or index) resolves."""
        if isinstance(key, int):
            return 0 <= key < len(self.bones)
        return key in self.by_name

    def index_of(self, key: str | int) -> int:
        """Resolve name or index to a bone index.

        Raises:
            BoneNotFoundError: If unknown.
        """
        if isinstance(key, int):
            if 0 <= key < len(self.bones):
                return key
            raise BoneNotFoundError(key)
        try:
            return self.by_name[key]
        except KeyError as exc:
            raise BoneNotFoundError(key) from exc

    def find(self, key: str | int) -> Bone:
        """Return the bone for ``key``.

        Raises:
            BoneNotFoundError: If unknown.
        """
        return self.bones[self.index_of(key)]

    def try_find(self, key: str | int) -> Bone | None:
        """Return bone or ``None``."""
        if not self.exists(key):
            return None
        return self.find(key)


__all__ = ["BoneLookup"]
