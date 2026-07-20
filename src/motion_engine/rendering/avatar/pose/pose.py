"""Pose abstraction — shared runtime pose API for M3+.

Hierarchy::

    Pose (ABC)
      ├── BindPose          (immutable reference / bind)
      └── AnimationPose     (mutable placeholder for M5)

Skinning, animation, retarget, and IK consume :class:`Pose` without caring
which specialization produced the transforms.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterator, Mapping, Sequence

import numpy as np

from motion_engine.rendering.avatar.pose.exceptions import PoseBoneNotFoundError
from motion_engine.rendering.avatar.pose.matrix_utils import (
    decompose_trs,
    identity_matrix,
    translation_of,
)
from motion_engine.rendering.avatar.pose.types import Mat4, PoseKind, Vec3


@dataclass(frozen=True, slots=True)
class BonePose:
    """Per-bone runtime pose sample (immutable snapshot)."""

    bone_id: int
    index: int
    name: str
    parent_index: int | None
    children: tuple[int, ...]
    local_matrix: Mat4
    global_matrix: Mat4
    rest_matrix: Mat4
    inverse_bind_matrix: Mat4
    translation: tuple[float, float, float]
    rotation_xyzw: tuple[float, float, float, float]
    scale: tuple[float, float, float]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "local_matrix",
            np.asarray(self.local_matrix, dtype=np.float64).reshape(4, 4).copy(),
        )
        object.__setattr__(
            self,
            "global_matrix",
            np.asarray(self.global_matrix, dtype=np.float64).reshape(4, 4).copy(),
        )
        object.__setattr__(
            self,
            "rest_matrix",
            np.asarray(self.rest_matrix, dtype=np.float64).reshape(4, 4).copy(),
        )
        object.__setattr__(
            self,
            "inverse_bind_matrix",
            np.asarray(self.inverse_bind_matrix, dtype=np.float64).reshape(4, 4).copy(),
        )
        object.__setattr__(self, "metadata", dict(self.metadata))
        object.__setattr__(self, "children", tuple(int(c) for c in self.children))

    def clone(self) -> BonePose:
        """Return an independently owned copy (new object + copied matrices/metadata)."""
        return BonePose(
            bone_id=self.bone_id,
            index=self.index,
            name=self.name,
            parent_index=self.parent_index,
            children=self.children,
            local_matrix=np.asarray(self.local_matrix, dtype=np.float64).copy(),
            global_matrix=np.asarray(self.global_matrix, dtype=np.float64).copy(),
            rest_matrix=np.asarray(self.rest_matrix, dtype=np.float64).copy(),
            inverse_bind_matrix=np.asarray(self.inverse_bind_matrix, dtype=np.float64).copy(),
            translation=self.translation,
            rotation_xyzw=self.rotation_xyzw,
            scale=self.scale,
            metadata=dict(self.metadata),
        )

    @property
    def world_position(self) -> tuple[float, float, float]:
        """World-space translation of the bone."""
        t = translation_of(self.global_matrix)
        return (float(t[0]), float(t[1]), float(t[2]))

    @classmethod
    def from_matrices(
        cls,
        *,
        bone_id: int,
        index: int,
        name: str,
        parent_index: int | None,
        children: Sequence[int],
        local_matrix: Mat4,
        global_matrix: Mat4,
        rest_matrix: Mat4 | None = None,
        inverse_bind_matrix: Mat4,
        metadata: Mapping[str, Any] | None = None,
    ) -> BonePose:
        """Build a BonePose, decomposing local TRS automatically."""
        t, q, s = decompose_trs(local_matrix)
        rest = global_matrix if rest_matrix is None else rest_matrix
        return cls(
            bone_id=bone_id,
            index=index,
            name=name,
            parent_index=parent_index,
            children=tuple(children),
            local_matrix=local_matrix,
            global_matrix=global_matrix,
            rest_matrix=rest,
            inverse_bind_matrix=inverse_bind_matrix,
            translation=(float(t[0]), float(t[1]), float(t[2])),
            rotation_xyzw=(float(q[0]), float(q[1]), float(q[2]), float(q[3])),
            scale=(float(s[0]), float(s[1]), float(s[2])),
            metadata=metadata or {},
        )


class Pose(ABC):
    """Abstract runtime pose consumed by skinning / animation / retarget.

    Implementations must provide O(1) bone lookup and matrix accessors.
    """

    @property
    @abstractmethod
    def kind(self) -> PoseKind:
        """Pose specialization tag."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable pose name."""

    @property
    @abstractmethod
    def bone_count(self) -> int:
        """Number of bones in the pose."""

    @property
    @abstractmethod
    def bones(self) -> tuple[BonePose, ...]:
        """Ordered bone pose samples."""

    @abstractmethod
    def find(self, key: str | int) -> BonePose:
        """Find bone pose by name or index."""

    @abstractmethod
    def exists(self, key: str | int) -> bool:
        """Return True if ``key`` resolves."""

    def try_find(self, key: str | int) -> BonePose | None:
        """Return bone pose or ``None``."""
        if not self.exists(key):
            return None
        return self.find(key)

    def parent(self, key: str | int) -> BonePose | None:
        """Parent bone pose, or ``None`` for roots."""
        b = self.find(key)
        if b.parent_index is None:
            return None
        return self.bones[b.parent_index]

    def children(self, key: str | int) -> tuple[BonePose, ...]:
        """Direct children of ``key``."""
        b = self.find(key)
        return tuple(self.bones[i] for i in b.children)

    def world_transform(self, key: str | int) -> Mat4:
        """Global / world matrix."""
        return self.find(key).global_matrix

    def local_transform(self, key: str | int) -> Mat4:
        """Local matrix."""
        return self.find(key).local_matrix

    def inverse_bind(self, key: str | int) -> Mat4:
        """Inverse bind matrix."""
        return self.find(key).inverse_bind_matrix

    def rest_transform(self, key: str | int) -> Mat4:
        """Rest / bind world matrix."""
        return self.find(key).rest_matrix

    def world_position(self, key: str | int) -> tuple[float, float, float]:
        """World-space position."""
        return self.find(key).world_position

    def rotation(self, key: str | int) -> tuple[float, float, float, float]:
        """Local rotation quaternion (xyzw)."""
        return self.find(key).rotation_xyzw

    def translation(self, key: str | int) -> tuple[float, float, float]:
        """Local translation."""
        return self.find(key).translation

    def scale(self, key: str | int) -> tuple[float, float, float]:
        """Local scale."""
        return self.find(key).scale

    def __iter__(self) -> Iterator[BonePose]:
        return iter(self.bones)

    def __len__(self) -> int:
        return self.bone_count

    def __getitem__(self, index: int) -> BonePose:
        return self.bones[index]


@dataclass(slots=True)
class AnimationPose(Pose):
    """Mutable pose placeholder for future animation runtime (M5).

    Today this copies bind data into editable buffers so downstream APIs can
    depend on :class:`Pose` without waiting for the animation milestone.
    """

    _name: str
    _bones: list[BonePose]
    _by_name: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._by_name = {b.name: b.index for b in self._bones}

    @property
    def kind(self) -> PoseKind:
        return PoseKind.ANIMATION

    @property
    def name(self) -> str:
        return self._name

    @property
    def bone_count(self) -> int:
        return len(self._bones)

    @property
    def bones(self) -> tuple[BonePose, ...]:
        return tuple(self._bones)

    def find(self, key: str | int) -> BonePose:
        if isinstance(key, int):
            if 0 <= key < len(self._bones):
                return self._bones[key]
            raise PoseBoneNotFoundError(key)
        try:
            return self._bones[self._by_name[key]]
        except KeyError as exc:
            raise PoseBoneNotFoundError(key) from exc

    def exists(self, key: str | int) -> bool:
        if isinstance(key, int):
            return 0 <= key < len(self._bones)
        return key in self._by_name

    def set_local_matrix(self, key: str | int, matrix: Mat4) -> None:
        """Replace a bone's local matrix (does not auto-propagate).

        Full FK refresh is deferred to the animation milestone; callers that
        need consistent worlds should rebuild via BindPoseFactory helpers.
        """
        idx = self.find(key).index
        old = self._bones[idx]
        self._bones[idx] = BonePose.from_matrices(
            bone_id=old.bone_id,
            index=old.index,
            name=old.name,
            parent_index=old.parent_index,
            children=old.children,
            local_matrix=matrix,
            global_matrix=old.global_matrix,
            rest_matrix=old.rest_matrix,
            inverse_bind_matrix=old.inverse_bind_matrix,
            metadata=old.metadata,
        )

    @classmethod
    def from_pose(cls, pose: Pose, *, name: str | None = None) -> AnimationPose:
        """Clone any pose into a mutable animation pose.

        Every :class:`BonePose` and every mutable ndarray / metadata mapping is
        independently owned. Mutating the result never affects ``pose``.
        """
        return cls(
            _name=name or f"anim:{pose.name}",
            _bones=[b.clone() for b in pose.bones],
        )

    @classmethod
    def identity(cls, names: Sequence[str], *, name: str = "AnimationPose") -> AnimationPose:
        """Build an all-identity animation pose (testing)."""
        eye = identity_matrix()
        bones = [
            BonePose.from_matrices(
                bone_id=i,
                index=i,
                name=nm,
                parent_index=None if i == 0 else i - 1,
                children=(i + 1,) if i + 1 < len(names) else (),
                local_matrix=eye,
                global_matrix=eye,
                inverse_bind_matrix=eye,
            )
            for i, nm in enumerate(names)
        ]
        # Fix children for non-chain: only chain parents above.
        fixed: list[BonePose] = []
        for i, b in enumerate(bones):
            parent = None if i == 0 else i - 1
            kids = (i + 1,) if i + 1 < len(names) else ()
            fixed.append(
                BonePose.from_matrices(
                    bone_id=b.bone_id,
                    index=i,
                    name=b.name,
                    parent_index=parent,
                    children=kids,
                    local_matrix=eye,
                    global_matrix=eye,
                    inverse_bind_matrix=eye,
                )
            )
        return cls(_name=name, _bones=fixed)


__all__ = ["BonePose", "Pose", "AnimationPose", "PoseKind"]
