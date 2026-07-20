"""
AXYX - Motion Engine
====================

Core SDK for the AXYX research platform: clinical gait reconstruction,
visualization.

Public API focuses on the domain model and the MATLAB → MotionDatabase
loader/parser pipeline.
"""

from __future__ import annotations

# Import loader for side effect: binds MotionDatabase.load implementation.
from motion_engine import loader as _loader  # noqa: F401
from motion_engine.constants import (
    UNKNOWN_UNITS,
    VALID_SESSION_CLASSIFICATIONS,
    VALID_TRAJECTORY_LAYOUTS,
)
from motion_engine.exceptions import (
    LoaderError,
    ModelValidationError,
    MotionEngineError,
    ParserError,
    SessionNotFoundError,
    SubjectNotFoundError,
    VariableNotFoundError,
)
from motion_engine.loader import DatasetLoader, MotionDatabaseLoader, load_motion_database
from motion_engine.models import (
    CenterOfMass,
    ClinicalMetric,
    JointAngle,
    JointCenter,
    Kinematics,
    Marker,
    Metadata,
    MotionDatabase,
    SegmentCOM,
    Session,
    Subject,
    Trajectory,
    ValidationReport,
)
from motion_engine.parser import MotionParser, parse_database
from motion_engine.skeleton import (
    Bone,
    Joint,
    Pose,
    Skeleton,
    SkeletonBuilder,
    SkeletonError,
    SkeletonValidator,
)
from motion_engine.skeleton_definition import SkeletonDefinition
from motion_engine.animation_clip import AnimationClip, AnimationClipError
from motion_engine.retarget import Retargeter, RetargetProfile
from motion_engine.exporter import AnimationJsonExporter, ExportFormat, create_exporter
from motion_engine.viewer import (
    MatplotlibViewer,
    Open3DViewer,
    PyVistaViewer,
    SkeletonViewer,
    Viewer,
    ViewerError,
)

__all__ = [
    "UNKNOWN_UNITS",
    "VALID_SESSION_CLASSIFICATIONS",
    "VALID_TRAJECTORY_LAYOUTS",
    "MotionEngineError",
    "ModelValidationError",
    "LoaderError",
    "ParserError",
    "SubjectNotFoundError",
    "SessionNotFoundError",
    "VariableNotFoundError",
    "ValidationReport",
    "Trajectory",
    "Marker",
    "JointAngle",
    "JointCenter",
    "CenterOfMass",
    "SegmentCOM",
    "ClinicalMetric",
    "Metadata",
    "Kinematics",
    "Session",
    "Subject",
    "MotionDatabase",
    "DatasetLoader",
    "MotionDatabaseLoader",
    "load_motion_database",
    "MotionParser",
    "parse_database",
    "Bone",
    "Joint",
    "Pose",
    "Skeleton",
    "SkeletonBuilder",
    "SkeletonError",
    "SkeletonValidator",
    "SkeletonDefinition",
    "Viewer",
    "SkeletonViewer",
    "PyVistaViewer",
    "Open3DViewer",
    "MatplotlibViewer",
    "ViewerError",
    "AnimationClip",
    "AnimationClipError",
    "Retargeter",
    "RetargetProfile",
    "AnimationJsonExporter",
    "ExportFormat",
    "create_exporter",
]

__version__ = "0.1.0"
