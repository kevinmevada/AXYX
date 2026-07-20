"""Immutable bone model for the M2 avatar skeleton runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np

from motion_engine.rendering.avatar.skeleton.transforms import Transform, identity_matrix
from motion_engine.rendering.avatar.skeleton.types import BoneFlag, BoneId, Mat4


@dataclass(frozen=True, slots=True)
class Bone:
    """Single bone in the canonical runtime skeleton.

    Bones are immutable after construction. Hierarchy links are stored as
    indices into the owning :class:`AvatarSkeleton`. Transform fields describe
    the **rest / bind** pose (animation poses live outside this object).
    """

    index: int
    name: str
    parent_index: int | None
    children: tuple[int, ...] = ()
    local_transform: Transform = field(default_factory=Transform.identity)
    world_transform: Mat4 | None = None
    rest_transform: Transform = field(default_factory=Transform.identity)
    inverse_bind: Mat4 | None = None
    bone_id: BoneId | None = None
    flags: BoneFlag = BoneFlag.NONE
    metadata: Mapping[str, Any] = field(default_factory=dict)
    user_data: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.bone_id is None:
            object.__setattr__(self, "bone_id", BoneId(self.index))
        if self.world_transform is None:
            object.__setattr__(self, "world_transform", identity_matrix())
        else:
            object.__setattr__(
                self,
                "world_transform",
                np.asarray(self.world_transform, dtype=np.float64).reshape(4, 4).copy(),
            )
        if self.inverse_bind is not None:
            object.__setattr__(
                self,
                "inverse_bind",
                np.asarray(self.inverse_bind, dtype=np.float64).reshape(4, 4).copy(),
            )
        # Freeze mapping views as plain dicts for hashability/immutability of content refs.
        object.__setattr__(self, "metadata", dict(self.metadata))
        object.__setattr__(self, "user_data", dict(self.user_data))
        object.__setattr__(self, "children", tuple(int(c) for c in self.children))

    # --- identity ---------------------------------------------------------

    @property
    def id(self) -> BoneId:
        """Unique bone identifier (stable for the lifetime of the skeleton)."""
        assert self.bone_id is not None
        return self.bone_id

    # --- TRS convenience --------------------------------------------------

    @property
    def translation(self) -> tuple[float, float, float]:
        """Local rest translation."""
        return self.local_transform.translation

    @property
    def rotation(self) -> tuple[float, float, float, float]:
        """Local rest rotation quaternion (xyzw)."""
        return self.local_transform.rotation_xyzw

    @property
    def scale(self) -> tuple[float, float, float]:
        """Local rest scale."""
        return self.local_transform.scale

    @property
    def local_matrix(self) -> Mat4:
        """Local rest matrix ``T @ R @ S``."""
        return self.local_transform.to_matrix()

    @property
    def world_matrix(self) -> Mat4:
        """World rest matrix (bind pose)."""
        assert self.world_transform is not None
        return self.world_transform

    @property
    def inverse_bind_matrix(self) -> Mat4 | None:
        """Inverse bind matrix, or ``None`` if not authored."""
        return self.inverse_bind

    # --- hierarchy queries (local to bone data) ---------------------------

    @property
    def is_root(self) -> bool:
        """True when this bone has no parent."""
        return self.parent_index is None

    @property
    def is_leaf(self) -> bool:
        """True when this bone has no children."""
        return len(self.children) == 0

    @property
    def child_count(self) -> int:
        """Number of direct children."""
        return len(self.children)

    @property
    def has_inverse_bind(self) -> bool:
        """True when an inverse bind matrix is present."""
        return self.inverse_bind is not None

    def with_children(self, children: tuple[int, ...]) -> Bone:
        """Return a copy with updated children indices."""
        return Bone(
            index=self.index,
            name=self.name,
            parent_index=self.parent_index,
            children=children,
            local_transform=self.local_transform,
            world_transform=self.world_matrix,
            rest_transform=self.rest_transform,
            inverse_bind=self.inverse_bind,
            bone_id=self.bone_id,
            flags=self.flags,
            metadata=self.metadata,
            user_data=self.user_data,
        )

    def with_world(self, world: Mat4) -> Bone:
        """Return a copy with an updated world rest matrix."""
        return Bone(
            index=self.index,
            name=self.name,
            parent_index=self.parent_index,
            children=self.children,
            local_transform=self.local_transform,
            world_transform=world,
            rest_transform=self.rest_transform,
            inverse_bind=self.inverse_bind,
            bone_id=self.bone_id,
            flags=self.flags,
            metadata=self.metadata,
            user_data=self.user_data,
        )


__all__ = ["Bone"]
