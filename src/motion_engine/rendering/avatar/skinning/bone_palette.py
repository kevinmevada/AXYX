"""Bone palette — compact remapping for skinning / future GPU upload."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from motion_engine.rendering.avatar.skinning.types import Int32Array


@dataclass(frozen=True, slots=True)
class BonePalette:
    """Maps palette slots → skeleton bone indices.

    Identity palettes use ``palette[i] = i``. Compact palettes only include
    bones referenced by weights (future GPU upload friendly).
    """

    bone_indices: Int32Array  # palette slot → skeleton bone index
    names: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "bone_indices",
            np.asarray(self.bone_indices, dtype=np.int32).copy(),
        )

    @property
    def size(self) -> int:
        return int(self.bone_indices.shape[0])

    @classmethod
    def identity(cls, bone_count: int, names: Sequence[str] | None = None) -> BonePalette:
        """Identity palette of size ``bone_count``."""
        nm = tuple(names) if names is not None else tuple(f"bone_{i}" for i in range(bone_count))
        return cls(bone_indices=np.arange(bone_count, dtype=np.int32), names=nm)

    @classmethod
    def from_used_bones(
        cls,
        used_bone_indices: np.ndarray,
        *,
        names: Sequence[str] | None = None,
    ) -> BonePalette:
        """Compact palette from unique used skeleton indices (sorted)."""
        uniq = np.unique(np.asarray(used_bone_indices, dtype=np.int32))
        uniq = uniq[uniq >= 0]
        if names is None:
            nm = tuple(f"bone_{int(i)}" for i in uniq)
        else:
            nm = tuple(
                names[int(i)] if int(i) < len(names) else f"bone_{int(i)}" for i in uniq
            )
        return cls(bone_indices=uniq, names=nm)

    def remap_weight_indices(self, joint_indices: np.ndarray) -> Int32Array:
        """Map skeleton bone indices in a weight table to palette slots."""
        inv = {int(b): slot for slot, b in enumerate(self.bone_indices.tolist())}
        out = np.full_like(joint_indices, -1, dtype=np.int32)
        flat_out = out.ravel()
        for i, b in enumerate(joint_indices.ravel()):
            bi = int(b)
            flat_out[i] = -1 if bi < 0 else inv.get(bi, -1)
        return out


__all__ = ["BonePalette"]
