"""Rest / bind-pose representation for future skinned avatars."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.floating]


@dataclass(slots=True)
class BindPose:
    """Named joint rest positions in world / model space."""

    joints: dict[str, FloatArray] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Sequence[float]]) -> BindPose:
        """Build a bind pose from name → XYZ mapping."""
        joints = {
            name: np.asarray(pos, dtype=float).reshape(3)
            for name, pos in mapping.items()
        }
        return cls(joints=joints)

    def get(self, name: str) -> FloatArray | None:
        """Return rest position for ``name``, if present."""
        return self.joints.get(name)


__all__ = ["BindPose"]
