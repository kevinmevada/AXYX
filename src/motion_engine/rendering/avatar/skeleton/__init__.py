"""M2 Avatar Skeleton Runtime — canonical skeletal representation.

This package is the **single source of truth** for avatar hierarchy, bind/rest
transforms, and bone queries. Imported M1 ``models.skeleton.AvatarSkeleton``
objects are converted via :class:`AvatarSkeletonFactory`.

Downstream systems (bind pose, skinning, animation, retarget, biomechanics)
must consume :class:`AvatarSkeleton` from this package — never raw import DTOs.
"""

from __future__ import annotations

from motion_engine.rendering.avatar.skeleton.avatar_skeleton import AvatarSkeleton
from motion_engine.rendering.avatar.skeleton.bind_data import BindData
from motion_engine.rendering.avatar.skeleton.bone import Bone
from motion_engine.rendering.avatar.skeleton.constants import RUNTIME_VERSION
from motion_engine.rendering.avatar.skeleton.exceptions import (
    BoneNotFoundError,
    SkeletonError,
    SkeletonFactoryError,
    SkeletonSerializationError,
    SkeletonValidationError,
)
from motion_engine.rendering.avatar.skeleton.factory import AvatarSkeletonFactory
from motion_engine.rendering.avatar.skeleton.hierarchy import HierarchyInfo
from motion_engine.rendering.avatar.skeleton.metadata import SkeletonMetadata
from motion_engine.rendering.avatar.skeleton.serialization import (
    export_debug,
    export_hierarchy,
    export_json,
    export_metadata,
    export_statistics,
    export_tree,
)
from motion_engine.rendering.avatar.skeleton.statistics import SkeletonStatistics
from motion_engine.rendering.avatar.skeleton.transforms import Transform
from motion_engine.rendering.avatar.skeleton.types import (
    BoneFlag,
    CoordinateSystem,
    LengthUnit,
)
from motion_engine.rendering.avatar.skeleton.validation import (
    SkeletonValidator,
    ValidationIssue,
    ValidationReport,
    validate_bones,
)

__all__ = [
    "AvatarSkeleton",
    "AvatarSkeletonFactory",
    "BindData",
    "Bone",
    "BoneFlag",
    "BoneNotFoundError",
    "CoordinateSystem",
    "HierarchyInfo",
    "LengthUnit",
    "RUNTIME_VERSION",
    "SkeletonError",
    "SkeletonFactoryError",
    "SkeletonMetadata",
    "SkeletonSerializationError",
    "SkeletonStatistics",
    "SkeletonValidationError",
    "SkeletonValidator",
    "Transform",
    "ValidationIssue",
    "ValidationReport",
    "export_debug",
    "export_hierarchy",
    "export_json",
    "export_metadata",
    "export_statistics",
    "export_tree",
    "validate_bones",
]
