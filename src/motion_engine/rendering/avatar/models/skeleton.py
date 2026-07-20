"""Skeleton models for Milestone 1 (hierarchy + bind matrices only)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.floating]


@dataclass(frozen=True, slots=True)
class BoneData:
    """Single bone in an avatar skeleton (rest / bind)."""

    index: int
    name: str
    parent_index: int | None
    local_translation: tuple[float, float, float] = (0.0, 0.0, 0.0)
    bind_world: FloatArray | None = None
    inverse_bind: FloatArray | None = None

    def __post_init__(self) -> None:
        if self.bind_world is not None:
            object.__setattr__(
                self, "bind_world", np.asarray(self.bind_world, dtype=np.float64).copy()
            )
        if self.inverse_bind is not None:
            object.__setattr__(
                self,
                "inverse_bind",
                np.asarray(self.inverse_bind, dtype=np.float64).copy(),
            )


@dataclass(frozen=True, slots=True)
class AvatarSkeleton:
    """Immutable skeleton hierarchy (no animation in M1)."""

    name: str
    bones: tuple[BoneData, ...]
    root_indices: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if not self.root_indices and self.bones:
            roots = tuple(i for i, b in enumerate(self.bones) if b.parent_index is None)
            object.__setattr__(self, "root_indices", roots or (0,))

    @property
    def bone_count(self) -> int:
        return len(self.bones)

    def index_of(self, name: str) -> int:
        """Return bone index by name.

        Raises:
            KeyError: If unknown.
        """
        for bone in self.bones:
            if bone.name == name:
                return bone.index
        raise KeyError(name)

    def try_bone(self, name: str) -> BoneData | None:
        """Return bone by name or ``None``."""
        for bone in self.bones:
            if bone.name == name:
                return bone
        return None


__all__ = ["BoneData", "AvatarSkeleton"]
