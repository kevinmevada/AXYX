"""Core retarget types — MotionSkeleton / MotionPose → AnimationPose bridge."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterator, Mapping, Sequence

import numpy as np
from numpy.typing import NDArray

from motion_engine.rendering.avatar.retarget.constants import (
    QUAT_IDENTITY,
    VEC3_ONE,
    VEC3_ZERO,
)

FloatArray = NDArray[np.floating[Any]]
Quat = tuple[float, float, float, float]  # xyzw
Vec3 = tuple[float, float, float]


class UpAxis(str, Enum):
    X = "x"
    Y = "y"
    Z = "z"


class ForwardAxis(str, Enum):
    X = "x"
    Y = "y"
    Z = "z"


class Handedness(str, Enum):
    LEFT = "left"
    RIGHT = "right"


class MappingKind(str, Enum):
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    OPTIONAL = "optional"
    VIRTUAL = "virtual"


class RootMotionMode(str, Enum):
    WORLD = "world"
    IN_PLACE = "in_place"
    EXTRACT = "extract"


class FilterKind(str, Enum):
    NONE = "none"
    MOVING_AVERAGE = "moving_average"
    BUTTERWORTH = "butterworth"
    SAVITZKY_GOLAY = "savitzky_golay"
    KALMAN = "kalman"


@dataclass(frozen=True, slots=True)
class CoordinateSystem:
    """Coordinate frame descriptor for automatic basis conversion."""

    up: UpAxis = UpAxis.Z
    forward: ForwardAxis = ForwardAxis.X
    handedness: Handedness = Handedness.RIGHT
    units_per_meter: float = 1.0
    name: str = "axyx"

    def key(self) -> str:
        return (
            f"{self.name}:{self.up.value}:{self.forward.value}:"
            f"{self.handedness.value}:{self.units_per_meter:g}"
        )


# Common presets
AXYX_COORDS = CoordinateSystem(up=UpAxis.Z, forward=ForwardAxis.X, handedness=Handedness.RIGHT, name="axyx")
Y_UP_RIGHT = CoordinateSystem(up=UpAxis.Y, forward=ForwardAxis.Z, handedness=Handedness.RIGHT, name="y_up")
UNREAL_COORDS = CoordinateSystem(up=UpAxis.Z, forward=ForwardAxis.X, handedness=Handedness.LEFT, name="unreal")
GLTF_COORDS = CoordinateSystem(up=UpAxis.Y, forward=ForwardAxis.Z, handedness=Handedness.RIGHT, name="gltf")


@dataclass(frozen=True, slots=True)
class MotionJoint:
    """One joint in a motion (source) skeleton."""

    name: str
    parent: str | None
    index: int
    rest_translation: Vec3 = VEC3_ZERO
    rest_rotation_xyzw: Quat = QUAT_IDENTITY
    optional: bool = False
    virtual: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MotionSkeleton:
    """Source motion skeleton (clinical / mocap / BVH / etc.)."""

    name: str
    joints: tuple[MotionJoint, ...]
    coordinate_system: CoordinateSystem = AXYX_COORDS
    root: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "joints", tuple(self.joints))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def joint_names(self) -> tuple[str, ...]:
        return tuple(j.name for j in self.joints)

    def find(self, name: str) -> MotionJoint | None:
        for j in self.joints:
            if j.name == name:
                return j
        return None

    def index_of(self, name: str) -> int:
        for j in self.joints:
            if j.name == name:
                return j.index
        raise KeyError(name)

    def children_of(self, name: str) -> list[str]:
        return [j.name for j in self.joints if j.parent == name]

    def __iter__(self) -> Iterator[MotionJoint]:
        return iter(self.joints)

    def __len__(self) -> int:
        return len(self.joints)


@dataclass(frozen=True, slots=True)
class JointSample:
    """Per-joint sample at a motion frame (quaternion-only rotations)."""

    name: str
    translation: Vec3 = VEC3_ZERO
    rotation_xyzw: Quat = QUAT_IDENTITY
    scale: Vec3 = VEC3_ONE
    world_position: Vec3 | None = None
    valid: bool = True

    def with_rotation(self, q: Quat) -> JointSample:
        return JointSample(
            name=self.name,
            translation=self.translation,
            rotation_xyzw=q,
            scale=self.scale,
            world_position=self.world_position,
            valid=self.valid,
        )


@dataclass(frozen=True, slots=True)
class MotionPose:
    """One source pose / frame ready for retargeting."""

    joints: Mapping[str, JointSample]
    time: float = 0.0
    index: int = 0
    root_translation: Vec3 | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "joints", dict(self.joints))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def get(self, name: str) -> JointSample | None:
        return self.joints.get(name)

    def names(self) -> list[str]:
        return list(self.joints.keys())


@dataclass(frozen=True, slots=True)
class BoneMapEntry:
    """Single source→target bone binding (supports multi-target)."""

    source: str
    targets: tuple[str, ...]
    kind: MappingKind = MappingKind.ONE_TO_ONE
    weight: float = 1.0
    optional: bool = False
    pre_rotation_xyzw: Quat = QUAT_IDENTITY
    post_rotation_xyzw: Quat = QUAT_IDENTITY
    copy_translation: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.targets, str):
            object.__setattr__(self, "targets", (self.targets,))
        else:
            object.__setattr__(self, "targets", tuple(self.targets))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def primary_target(self) -> str:
        return self.targets[0]


@dataclass(frozen=True, slots=True)
class JointLimit:
    """Soft/hard DOF limits in radians about local XYZ axes."""

    bone: str
    min_xyz: Vec3 = (-np.pi, -np.pi, -np.pi)  # type: ignore[assignment]
    max_xyz: Vec3 = (np.pi, np.pi, np.pi)  # type: ignore[assignment]
    locked: bool = False
    preferred_axis: Vec3 | None = None
    hard: bool = False


@dataclass(frozen=True, slots=True)
class MappingProfile:
    """Named retarget mapping profile (MATLAB, Mixamo, MetaHuman, custom)."""

    name: str
    source_skeleton: str
    target_skeleton: str
    bones: tuple[BoneMapEntry, ...]
    root_source: str = "Pelvis"
    root_target: str = "pelvis"
    source_coords: CoordinateSystem = AXYX_COORDS
    target_coords: CoordinateSystem = Y_UP_RIGHT
    ignore_source: tuple[str, ...] = ()
    ignore_target: tuple[str, ...] = ()
    joint_limits: tuple[JointLimit, ...] = ()
    chains: Mapping[str, Sequence[str]] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "bones", tuple(self.bones))
        object.__setattr__(self, "ignore_source", tuple(self.ignore_source))
        object.__setattr__(self, "ignore_target", tuple(self.ignore_target))
        object.__setattr__(self, "joint_limits", tuple(self.joint_limits))
        object.__setattr__(self, "chains", {k: list(v) for k, v in dict(self.chains).items()})
        object.__setattr__(self, "metadata", dict(self.metadata))

    def source_to_targets(self) -> dict[str, tuple[str, ...]]:
        return {e.source: e.targets for e in self.bones}

    def target_to_sources(self) -> dict[str, list[str]]:
        inv: dict[str, list[str]] = {}
        for e in self.bones:
            for t in e.targets:
                inv.setdefault(t, []).append(e.source)
        return inv

    def entry_for_source(self, source: str) -> BoneMapEntry | None:
        for e in self.bones:
            if e.source == source:
                return e
        return None

    def mapped_sources(self) -> set[str]:
        return {e.source for e in self.bones}

    def mapped_targets(self) -> set[str]:
        out: set[str] = set()
        for e in self.bones:
            out.update(e.targets)
        return out


@dataclass
class RetargetStatistics:
    """Per-session / per-frame retarget statistics."""

    mapped_bones: int = 0
    ignored_source: int = 0
    ignored_target: int = 0
    missing_source: int = 0
    missing_target: int = 0
    scale_ratio: float = 1.0
    constraint_violations: int = 0
    coverage: float = 0.0
    frame_time_ns: int = 0
    retarget_time_ns: int = 0
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "mapped_bones": self.mapped_bones,
            "ignored_source": self.ignored_source,
            "ignored_target": self.ignored_target,
            "missing_source": self.missing_source,
            "missing_target": self.missing_target,
            "scale_ratio": self.scale_ratio,
            "constraint_violations": self.constraint_violations,
            "coverage": self.coverage,
            "frame_time_ns": self.frame_time_ns,
            "retarget_time_ns": self.retarget_time_ns,
            **self.extra,
        }


__all__ = [
    "FloatArray",
    "Quat",
    "Vec3",
    "UpAxis",
    "ForwardAxis",
    "Handedness",
    "MappingKind",
    "RootMotionMode",
    "FilterKind",
    "CoordinateSystem",
    "AXYX_COORDS",
    "Y_UP_RIGHT",
    "UNREAL_COORDS",
    "GLTF_COORDS",
    "MotionJoint",
    "MotionSkeleton",
    "JointSample",
    "MotionPose",
    "BoneMapEntry",
    "JointLimit",
    "MappingProfile",
    "RetargetStatistics",
]
