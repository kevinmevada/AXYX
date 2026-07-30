"""AXYX Motion Retargeting Engine (M6).

Converts arbitrary skeletal motion into an AvatarSkeleton AnimationPose
while preserving biomechanics. Does not mutate motion data, AvatarSkeleton,
BindPose, AnimationRuntime, SkinningRuntime, or Viewer public APIs.
"""

from __future__ import annotations

from motion_engine.rendering.avatar.retarget.constants import RUNTIME_VERSION, SCHEMA_VERSION
from motion_engine.rendering.avatar.retarget.exceptions import (
    ConstraintError,
    CoordinateError,
    MappingError,
    RetargetError,
    ValidationError,
)
from motion_engine.rendering.avatar.retarget.factory import RetargetFactory
from motion_engine.rendering.avatar.retarget.legacy import AvatarRetarget, AvatarRetargetProfile
from motion_engine.rendering.avatar.retarget.mapping_factory import MappingFactory
from motion_engine.rendering.avatar.retarget.retarget_engine import RetargetEngine
from motion_engine.rendering.avatar.retarget.retarget_context import RetargetContext
from motion_engine.rendering.avatar.retarget.retarget_session import RetargetSession
from motion_engine.rendering.avatar.retarget.types import (
    AXYX_COORDS,
    GLTF_COORDS,
    UNREAL_COORDS,
    Y_UP_RIGHT,
    BoneMapEntry,
    CoordinateSystem,
    FilterKind,
    JointSample,
    MappingKind,
    MappingProfile,
    MotionJoint,
    MotionPose,
    MotionSkeleton,
    RetargetStatistics,
    RootMotionMode,
)

__all__ = [
    "RUNTIME_VERSION",
    "SCHEMA_VERSION",
    "RetargetError",
    "MappingError",
    "ValidationError",
    "CoordinateError",
    "ConstraintError",
    "RetargetEngine",
    "RetargetContext",
    "RetargetSession",
    "RetargetFactory",
    "MappingFactory",
    "MappingProfile",
    "BoneMapEntry",
    "MappingKind",
    "MotionSkeleton",
    "MotionJoint",
    "MotionPose",
    "JointSample",
    "CoordinateSystem",
    "AXYX_COORDS",
    "Y_UP_RIGHT",
    "UNREAL_COORDS",
    "GLTF_COORDS",
    "RootMotionMode",
    "FilterKind",
    "RetargetStatistics",
    "AvatarRetarget",
    "AvatarRetargetProfile",
]
