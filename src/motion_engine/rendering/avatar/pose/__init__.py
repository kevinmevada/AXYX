"""M3 Bind Pose Runtime — Pose abstraction + immutable BindPose.

Architecture::

    AvatarSkeleton (structure, M2, immutable)
            │
            ▼  BindPoseFactory
    Pose (ABC)
      ├── BindPose        — immutable reference / bind / rest
      └── AnimationPose   — mutable placeholder for M5

Downstream systems (skinning, animation, retarget, IK) must consume :class:`Pose`.
"""

from __future__ import annotations

from motion_engine.rendering.avatar.pose.bind_matrix import BindMatrixSet
from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.pose.constants import RUNTIME_VERSION
from motion_engine.rendering.avatar.pose.coordinate_system import PoseCoordinateSystem
from motion_engine.rendering.avatar.pose.exceptions import (
    PoseBoneNotFoundError,
    PoseError,
    PoseFactoryError,
    PoseSerializationError,
    PoseValidationError,
)
from motion_engine.rendering.avatar.pose.pose import AnimationPose, BonePose, Pose
from motion_engine.rendering.avatar.pose.pose_cache import PoseCache
from motion_engine.rendering.avatar.pose.pose_factory import BindPoseFactory, PoseFactory
from motion_engine.rendering.avatar.pose.pose_serialization import (
    export_debug_report,
    export_hierarchy,
    export_json,
    export_matrices,
    export_pose_dict,
)
from motion_engine.rendering.avatar.pose.pose_statistics import PoseStatistics
from motion_engine.rendering.avatar.pose.pose_validation import (
    PoseValidationIssue,
    PoseValidationReport,
    PoseValidator,
    validate_pose,
)
from motion_engine.rendering.avatar.pose.rest_pose import RestPoseInfo
from motion_engine.rendering.avatar.pose.types import (
    Handedness,
    PoseKind,
    RestPoseKind,
)

__all__ = [
    "AnimationPose",
    "BindMatrixSet",
    "BindPose",
    "BindPoseFactory",
    "BonePose",
    "Handedness",
    "Pose",
    "PoseBoneNotFoundError",
    "PoseCache",
    "PoseCoordinateSystem",
    "PoseError",
    "PoseFactory",
    "PoseFactoryError",
    "PoseKind",
    "PoseSerializationError",
    "PoseStatistics",
    "PoseValidationError",
    "PoseValidationIssue",
    "PoseValidationReport",
    "PoseValidator",
    "RUNTIME_VERSION",
    "RestPoseInfo",
    "RestPoseKind",
    "export_debug_report",
    "export_hierarchy",
    "export_json",
    "export_matrices",
    "export_pose_dict",
    "validate_pose",
]
