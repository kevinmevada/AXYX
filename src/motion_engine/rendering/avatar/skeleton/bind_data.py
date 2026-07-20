"""Bind / rest pose data helpers (inverse bind matrices)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from motion_engine.rendering.avatar.skeleton.bone import Bone
from motion_engine.rendering.avatar.skeleton.transforms import identity_matrix, invert_affine
from motion_engine.rendering.avatar.skeleton.types import Mat4


@dataclass(frozen=True, slots=True)
class BindData:
    """Rest-world and inverse-bind buffers aligned to bone indices."""

    rest_world: tuple[Mat4, ...]
    inverse_bind: tuple[Mat4 | None, ...]

    @property
    def bone_count(self) -> int:
        return len(self.rest_world)

    def rest_world_at(self, index: int) -> Mat4:
        return self.rest_world[index]

    def inverse_bind_at(self, index: int) -> Mat4 | None:
        return self.inverse_bind[index]


def ensure_inverse_bind(world: Mat4, ibm: Mat4 | None) -> Mat4:
    """Return authored IBM or ``inv(world)`` when missing."""
    if ibm is not None:
        return np.asarray(ibm, dtype=np.float64).reshape(4, 4).copy()
    return invert_affine(world)


def bind_data_from_bones(bones: tuple[Bone, ...]) -> BindData:
    """Extract bind buffers from bones."""
    rest = tuple(
        np.asarray(b.world_matrix, dtype=np.float64).copy() for b in bones
    )
    ibm = tuple(
        None
        if b.inverse_bind is None
        else np.asarray(b.inverse_bind, dtype=np.float64).copy()
        for b in bones
    )
    return BindData(rest_world=rest, inverse_bind=ibm)


def identity_bind(n: int) -> BindData:
    """Identity rest + IBM for ``n`` bones (testing / procedural)."""
    eye = identity_matrix()
    rest = tuple(eye.copy() for _ in range(n))
    ibm = tuple(eye.copy() for _ in range(n))
    return BindData(rest_world=rest, inverse_bind=ibm)


__all__ = [
    "BindData",
    "ensure_inverse_bind",
    "bind_data_from_bones",
    "identity_bind",
]
