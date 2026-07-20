"""
Skeleton Builder - Human Reconstruction foundation.

Converts :class:`~motion_engine.models.Session` kinematics into a
renderer-independent :class:`Skeleton` graph (joints, bones, per-frame poses).

Marker → joint mappings are loaded from ``config/skeleton_definition.yaml``.
No rendering, Blender, Unreal, physics, or IK logic lives here.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from motion_engine.constants import (
    COORDINATE_DIMENSION,
    LAYOUT_3_BY_N,
    LAYOUT_N_BY_3,
    UNKNOWN_UNITS,
)
from motion_engine.constraints import ConstraintConfig
from motion_engine.coordinate_system import CoordinateSystemConfig
from motion_engine.exceptions import MotionEngineError
from motion_engine.models import Session, ValidationReport
from motion_engine.skeleton_definition import (
    DEFAULT_SKELETON_DEFINITION_PATH,
    JointDefinition,
    JointSourceSpec,
    SkeletonDefinition,
)

logger = logging.getLogger(__name__)

FloatArray = NDArray[np.floating[Any]]

DEFAULT_CONSTRAINTS_PATH = Path("config/bone_constraints.yaml")
DEFAULT_COORDINATE_SYSTEM_PATH = Path("config/coordinate_system.yaml")


class SkeletonError(MotionEngineError):
    """Raised for fatal skeleton configuration / build failures."""


# ---------------------------------------------------------------------------
# Domain objects
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class Joint:
    """Named skeletal joint with optional parent and marker provenance.

    Attributes:
        name: Joint identifier from the skeleton definition.
        parent: Parent joint name, or None for the root.
        children: Child joint names.
        source_markers: Marker names used when the joint was resolved.
        source_type: Winning source type (``markers`` / ``joint_center``).
    """

    name: str
    parent: str | None = None
    children: list[str] = field(default_factory=list)
    source_markers: list[str] = field(default_factory=list)
    source_type: str | None = None

    def validate(self) -> ValidationReport:
        """Lightweight joint validation."""
        report = ValidationReport()
        if not self.name:
            report.errors.append("Joint.name must be non-empty")
        if self.parent == self.name:
            report.errors.append(f"Joint {self.name!r} cannot be its own parent")
        return report

    def __repr__(self) -> str:
        return (
            f"Joint(name={self.name!r}, parent={self.parent!r}, "
            f"children={len(self.children)})"
        )


@dataclass(slots=True)
class Bone:
    """Directed bone between a parent joint and a child joint.

    Attributes:
        name: Bone identifier from the skeleton definition.
        parent_joint: Proximal joint name.
        child_joint: Distal joint name.
        length: Mean Euclidean length across resolved frames (Unknown units).
        lengths: Per-frame lengths (NaN where either endpoint is missing).
    """

    name: str
    parent_joint: str
    child_joint: str
    length: float | None = None
    lengths: FloatArray | None = None
    units: str = UNKNOWN_UNITS

    def validate(self) -> ValidationReport:
        """Lightweight bone validation."""
        report = ValidationReport()
        if not self.name:
            report.errors.append("Bone.name must be non-empty")
        if self.parent_joint == self.child_joint:
            report.errors.append(
                f"Bone {self.name!r} parent_joint and child_joint are identical"
            )
        if self.length is not None and self.length < 0:
            report.errors.append(f"Bone {self.name!r} length must be >= 0")
        if self.units == UNKNOWN_UNITS:
            report.infos.append("bone units are Unknown")
        return report

    def __repr__(self) -> str:
        return (
            f"Bone(name={self.name!r}, {self.parent_joint!r}->{self.child_joint!r}, "
            f"length={self.length!r})"
        )


@dataclass(slots=True)
class Pose:
    """One skeleton pose at a single frame index.

    Attributes:
        frame_index: Zero-based frame index into the session trajectories.
        joint_positions: Mapping of joint name → XYZ position ``(3,)``.
        missing_joints: Joints that could not be resolved at this frame.
    """

    frame_index: int
    joint_positions: dict[str, FloatArray] = field(default_factory=dict)
    missing_joints: list[str] = field(default_factory=list)

    def get_position(self, joint_name: str) -> FloatArray | None:
        """Return a joint position or None if unresolved."""
        return self.joint_positions.get(joint_name)

    def validate(self) -> ValidationReport:
        """Lightweight pose validation."""
        report = ValidationReport()
        if self.frame_index < 0:
            report.errors.append("Pose.frame_index must be >= 0")
        for name, position in self.joint_positions.items():
            array = np.asarray(position)
            if array.shape != (COORDINATE_DIMENSION,):
                report.errors.append(
                    f"Pose joint {name!r} position shape {array.shape} "
                    f"!= ({COORDINATE_DIMENSION},)"
                )
        return report

    def __repr__(self) -> str:
        return (
            f"Pose(frame_index={self.frame_index}, "
            f"joints={len(self.joint_positions)}, "
            f"missing={len(self.missing_joints)})"
        )


@dataclass(slots=True)
class Skeleton:
    """Renderer-independent skeletal reconstruction of one Session.

    Designed as a neutral exchange structure for future OpenSim / BVH / FBX /
    glTF / URDF / USD / ROS / Blender / Unity / Unreal / Omniverse exporters.
    """

    name: str
    subject_id: str
    session_name: str
    root_joint: str
    joints: dict[str, Joint] = field(default_factory=dict)
    bones: dict[str, Bone] = field(default_factory=dict)
    poses: list[Pose] = field(default_factory=list)
    n_frames: int = 0
    sampling_rate_hz: float | None = None
    units: str = UNKNOWN_UNITS
    coordinate_system: str = "lab"
    missing_markers: list[str] = field(default_factory=list)
    unresolved_joints: list[str] = field(default_factory=list)
    definition_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def frame_count(self) -> int:
        """Alias for :attr:`n_frames` (certification / external API)."""
        return int(self.n_frames)

    def list_joints(self) -> list[str]:
        """Return sorted joint names."""
        return sorted(self.joints)

    def list_bones(self) -> list[str]:
        """Return sorted bone names."""
        return sorted(self.bones)

    def get_joint(self, name: str) -> Joint:
        """Return a joint by name."""
        try:
            return self.joints[name]
        except KeyError as exc:
            raise SkeletonError(f"Joint not found: {name!r}") from exc

    def get_bone(self, name: str) -> Bone:
        """Return a bone by name."""
        try:
            return self.bones[name]
        except KeyError as exc:
            raise SkeletonError(f"Bone not found: {name!r}") from exc

    def get_pose(self, frame_index: int) -> Pose:
        """Return the pose at ``frame_index``."""
        if frame_index < 0 or frame_index >= len(self.poses):
            raise SkeletonError(
                f"frame_index {frame_index} out of range [0, {len(self.poses)})"
            )
        return self.poses[frame_index]

    def bone_lengths(self) -> dict[str, float | None]:
        """Return mean bone lengths keyed by bone name."""
        return {name: bone.length for name, bone in self.bones.items()}

    def children_of(self, joint_name: str) -> list[str]:
        """Return child joint names for the hierarchy."""
        joint = self.joints.get(joint_name)
        return list(joint.children) if joint else []

    def validate(self) -> ValidationReport:
        """Validate skeleton structure and nested objects."""
        report = ValidationReport()
        if not self.name:
            report.errors.append("Skeleton.name must be non-empty")
        if self.root_joint not in self.joints:
            report.errors.append(
                f"root_joint {self.root_joint!r} is not present in joints"
            )
        if self.n_frames != len(self.poses):
            report.errors.append(
                f"n_frames ({self.n_frames}) != len(poses) ({len(self.poses)})"
            )
        for key, joint in self.joints.items():
            if key != joint.name:
                report.errors.append(
                    f"Joint key {key!r} != joint.name {joint.name!r}"
                )
            report.extend(joint.validate())
        for key, bone in self.bones.items():
            if key != bone.name:
                report.errors.append(f"Bone key {key!r} != bone.name {bone.name!r}")
            if bone.parent_joint not in self.joints:
                report.errors.append(
                    f"Bone {bone.name!r} parent_joint {bone.parent_joint!r} missing"
                )
            if bone.child_joint not in self.joints:
                report.errors.append(
                    f"Bone {bone.name!r} child_joint {bone.child_joint!r} missing"
                )
            report.extend(bone.validate())
        for pose in self.poses:
            report.extend(pose.validate())
        if self.missing_markers:
            report.warnings.append(
                f"Missing markers: {sorted(self.missing_markers)}"
            )
        if self.unresolved_joints:
            report.warnings.append(
                f"Unresolved joints: {sorted(self.unresolved_joints)}"
            )
        if self.units == UNKNOWN_UNITS:
            report.infos.append("skeleton units are Unknown")
        return report

    def __repr__(self) -> str:
        return (
            f"Skeleton(name={self.name!r}, subject={self.subject_id!r}, "
            f"session={self.session_name!r}, joints={len(self.joints)}, "
            f"bones={len(self.bones)}, frames={self.n_frames})"
        )


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------


def trajectory_as_n_by_3(
    coordinates: FloatArray,
    layout: str | None,
) -> FloatArray:
    """Normalize trajectory coordinates to ``(N, 3)`` without assuming orientation.

    Args:
        coordinates: Raw trajectory array.
        layout: ``"N,3"``, ``"3,N"``, or None (auto-detect via size-3 axis).

    Returns:
        Array with shape ``(n_frames, 3)``.
    """
    array = np.asarray(coordinates, dtype=float)
    if array.ndim != 2:
        raise SkeletonError(f"Trajectory must be 2D, got shape {array.shape}")

    if layout == LAYOUT_N_BY_3:
        if array.shape[1] != COORDINATE_DIMENSION:
            raise SkeletonError(
                f"layout N,3 requires shape[1]==3, got {array.shape}"
            )
        return array
    if layout == LAYOUT_3_BY_N:
        if array.shape[0] != COORDINATE_DIMENSION:
            raise SkeletonError(
                f"layout 3,N requires shape[0]==3, got {array.shape}"
            )
        return array.T

    # Auto-detect
    if array.shape[1] == COORDINATE_DIMENSION and array.shape[0] != COORDINATE_DIMENSION:
        return array
    if array.shape[0] == COORDINATE_DIMENSION and array.shape[1] != COORDINATE_DIMENSION:
        return array.T
    raise SkeletonError(
        f"Cannot normalize trajectory layout for shape {array.shape} "
        f"(layout={layout!r})"
    )


def _nan_position() -> FloatArray:
    return np.full((COORDINATE_DIMENSION,), np.nan, dtype=float)


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


class SkeletonValidator:
    """Validate skeleton completeness against definition + soft constraints."""

    def __init__(
        self,
        definition: SkeletonDefinition,
        constraints: ConstraintConfig | None = None,
    ) -> None:
        self.definition = definition
        self.constraints = constraints or ConstraintConfig()

    def validate(self, skeleton: Skeleton) -> ValidationReport:
        """Run structural + soft anthropometric validation."""
        report = skeleton.validate()

        # Completeness: required markers from definition ∩ session gaps
        missing_required = sorted(
            set(self.definition.required_markers) & set(skeleton.missing_markers)
        )
        if missing_required:
            report.warnings.append(
                f"Required markers missing from session: {missing_required}"
            )

        for bone_name in self.constraints.required_bones:
            bone = skeleton.bones.get(bone_name)
            if bone is None:
                report.errors.append(f"Required bone missing: {bone_name}")
                continue
            if bone.length is None or not np.isfinite(bone.length):
                report.warnings.append(
                    f"Required bone {bone_name!r} has unresolved mean length"
                )
                continue
            constraint = self.constraints.bones.get(bone_name)
            if constraint is None:
                continue
            if bone.length < constraint.min_length or bone.length > constraint.max_length:
                message = (
                    f"Bone {bone_name!r} length {bone.length:.4g} outside "
                    f"[{constraint.min_length}, {constraint.max_length}]"
                )
                if self.constraints.enforce_hard_limits:
                    report.errors.append(message)
                else:
                    report.warnings.append(message)

            if bone.lengths is not None and np.isfinite(bone.length) and bone.length > 0:
                finite = bone.lengths[np.isfinite(bone.lengths)]
                if finite.size:
                    ratios = finite / bone.length
                    if np.any(ratios < self.constraints.relative_min_ratio) or np.any(
                        ratios > self.constraints.relative_max_ratio
                    ):
                        report.warnings.append(
                            f"Bone {bone_name!r} has per-frame lengths outside "
                            f"relative ratio "
                            f"[{self.constraints.relative_min_ratio}, "
                            f"{self.constraints.relative_max_ratio}]"
                        )

        # Root must have no parent
        root = skeleton.joints.get(skeleton.root_joint)
        if root is not None and root.parent is not None:
            report.errors.append(
                f"Root joint {skeleton.root_joint!r} has parent {root.parent!r}"
            )

        return report


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


class SkeletonBuilder:
    """Build a :class:`Skeleton` from a MotionDatabase :class:`Session`.

    Configuration is loaded from YAML under ``config/``. Marker mappings are
    never hardcoded in this class.
    """

    def __init__(
        self,
        definition_path: str | Path | None = None,
        constraints_path: str | Path | None = None,
        coordinate_system_path: str | Path | None = None,
        *,
        log: logging.Logger | None = None,
    ) -> None:
        self.log = log or logger
        self.definition_path = Path(
            definition_path or DEFAULT_SKELETON_DEFINITION_PATH
        )
        self.constraints_path = Path(constraints_path or DEFAULT_CONSTRAINTS_PATH)
        self.coordinate_system_path = Path(
            coordinate_system_path or DEFAULT_COORDINATE_SYSTEM_PATH
        )

        if not self.definition_path.is_file():
            raise SkeletonError(
                f"Skeleton definition missing: {self.definition_path}"
            )

        self.definition = SkeletonDefinition.from_yaml(self.definition_path)
        self.constraints = (
            ConstraintConfig.from_yaml(self.constraints_path)
            if self.constraints_path.is_file()
            else ConstraintConfig()
        )
        self.coordinate_system = (
            CoordinateSystemConfig.from_yaml(self.coordinate_system_path)
            if self.coordinate_system_path.is_file()
            else CoordinateSystemConfig()
        )
        self.validator = SkeletonValidator(self.definition, self.constraints)
        self.log.info(
            "SkeletonBuilder ready (definition=%s, joints=%d, bones=%d)",
            self.definition.name,
            len(self.definition.joints),
            len(self.definition.bones),
        )

    # -- public API --------------------------------------------------------

    def build(self, session: Session) -> Skeleton:
        """Build a skeleton for one session.

        Args:
            session: Parsed MotionDatabase session.

        Returns:
            Populated :class:`Skeleton` with per-frame poses and bone lengths.
        """
        self.log.info(
            "Building skeleton for %s/%s",
            session.subject_id,
            session.name,
        )

        marker_series, missing_markers = self._collect_marker_series(session)
        joint_center_series = self._collect_joint_center_series(session)
        n_frames = self._resolve_frame_count(
            session, marker_series, joint_center_series
        )
        if n_frames <= 0:
            raise SkeletonError(
                f"Session {session.subject_id}/{session.name} has no usable frames"
            )

        joints = self._build_joint_graph()
        joint_positions, unresolved_joints, joint_source_meta = self._resolve_all_joints(
            n_frames=n_frames,
            marker_series=marker_series,
            joint_center_series=joint_center_series,
        )

        for joint_name, meta in joint_source_meta.items():
            joint = joints[joint_name]
            joint.source_type = meta.get("source_type")
            joint.source_markers = list(meta.get("source_markers") or [])

        poses = self._assemble_poses(n_frames, joint_positions, unresolved_joints)
        bones = self._build_bones(n_frames, joint_positions)

        skeleton = Skeleton(
            name=f"{session.subject_id}_{session.name}",
            subject_id=session.subject_id,
            session_name=session.name,
            root_joint=self.definition.root_joint,
            joints=joints,
            bones=bones,
            poses=poses,
            n_frames=n_frames,
            sampling_rate_hz=session.sampling_rate_hz,
            units=self.definition.units or UNKNOWN_UNITS,
            coordinate_system=self.definition.coordinate_system
            or self.coordinate_system.name,
            missing_markers=sorted(missing_markers),
            unresolved_joints=sorted(unresolved_joints),
            definition_name=self.definition.name,
            metadata={
                "definition_path": str(self.definition_path),
                "classification": session.classification,
                "trajectory_layout": session.trajectory_layout,
            },
        )

        report = self.validator.validate(skeleton)
        for warning in report.warnings:
            self.log.warning("%s/%s: %s", session.subject_id, session.name, warning)
        for error in report.errors:
            self.log.error("%s/%s: %s", session.subject_id, session.name, error)
        if report.errors:
            # Soft-complete skeletons with warnings are OK; only raise on hard errors.
            raise SkeletonError(
                f"Skeleton validation failed for {session.subject_id}/{session.name}: "
                + "; ".join(report.errors)
            )

        self.log.info(
            "Skeleton built: joints=%d bones=%d frames=%d missing_markers=%d",
            len(skeleton.joints),
            len(skeleton.bones),
            skeleton.n_frames,
            len(skeleton.missing_markers),
        )
        return skeleton

    # -- collection --------------------------------------------------------

    def _collect_marker_series(
        self,
        session: Session,
    ) -> tuple[dict[str, FloatArray], set[str]]:
        """Return ``{marker: (N,3)}`` and the set of referenced-but-missing markers."""
        needed = self.definition.required_source_markers()
        series: dict[str, FloatArray] = {}
        missing: set[str] = set()
        for name in sorted(needed):
            marker = session.kinematics.markers.get(name)
            if marker is None:
                missing.add(name)
                continue
            try:
                series[name] = trajectory_as_n_by_3(
                    marker.trajectory.coordinates,
                    marker.trajectory.layout,
                )
            except SkeletonError as exc:
                self.log.warning(
                    "Marker %s layout normalization failed: %s", name, exc
                )
                missing.add(name)
        return series, missing

    def _collect_joint_center_series(
        self,
        session: Session,
    ) -> dict[str, FloatArray]:
        """Return ``{joint_center: (N,3)}`` for available JC trajectories."""
        series: dict[str, FloatArray] = {}
        for name, center in session.kinematics.joint_centers.items():
            try:
                series[name] = trajectory_as_n_by_3(
                    center.trajectory.coordinates,
                    center.trajectory.layout,
                )
            except SkeletonError as exc:
                self.log.warning(
                    "Joint center %s layout normalization failed: %s", name, exc
                )
        return series

    def _resolve_frame_count(
        self,
        session: Session,
        marker_series: dict[str, FloatArray],
        joint_center_series: dict[str, FloatArray],
    ) -> int:
        """Determine frame count from session metadata or trajectory lengths."""
        if session.frame_count is not None and session.frame_count > 0:
            return int(session.frame_count)
        lengths = [arr.shape[0] for arr in marker_series.values()]
        lengths.extend(arr.shape[0] for arr in joint_center_series.values())
        if not lengths:
            return 0
        # Prefer the most common length to tolerate a malformed series.
        values, counts = np.unique(lengths, return_counts=True)
        return int(values[int(np.argmax(counts))])

    # -- hierarchy ---------------------------------------------------------

    def _build_joint_graph(self) -> dict[str, Joint]:
        """Instantiate Joint objects and wire parent/child links from YAML."""
        joints: dict[str, Joint] = {}
        for name, definition in self.definition.joints.items():
            joints[name] = Joint(name=name, parent=definition.parent, children=[])

        for name, joint in joints.items():
            if joint.parent is None:
                continue
            if joint.parent not in joints:
                raise SkeletonError(
                    f"Joint {name!r} parent {joint.parent!r} is not defined"
                )
            joints[joint.parent].children.append(name)

        if self.definition.root_joint not in joints:
            raise SkeletonError(
                f"root_joint {self.definition.root_joint!r} missing from definition"
            )
        return joints

    # -- joint resolution --------------------------------------------------

    def _resolve_all_joints(
        self,
        *,
        n_frames: int,
        marker_series: dict[str, FloatArray],
        joint_center_series: dict[str, FloatArray],
    ) -> tuple[dict[str, FloatArray], list[str], dict[str, dict[str, Any]]]:
        """Resolve every defined joint to an ``(N, 3)`` position series."""
        positions: dict[str, FloatArray] = {}
        unresolved: list[str] = []
        meta: dict[str, dict[str, Any]] = {}

        for joint_name, definition in self.definition.joints.items():
            series, source_meta = self._resolve_joint_series(
                definition,
                n_frames=n_frames,
                marker_series=marker_series,
                joint_center_series=joint_center_series,
            )
            if series is None:
                unresolved.append(joint_name)
                positions[joint_name] = np.full(
                    (n_frames, COORDINATE_DIMENSION), np.nan, dtype=float
                )
                meta[joint_name] = {"source_type": None, "source_markers": []}
                self.log.warning("Joint %s could not be resolved from any source", joint_name)
            else:
                positions[joint_name] = series
                meta[joint_name] = source_meta
        return positions, unresolved, meta

    def _resolve_joint_series(
        self,
        definition: JointDefinition,
        *,
        n_frames: int,
        marker_series: dict[str, FloatArray],
        joint_center_series: dict[str, FloatArray],
    ) -> tuple[FloatArray | None, dict[str, Any]]:
        """Try prioritized sources until one yields a usable series."""
        for source in sorted(definition.sources, key=lambda item: item.priority):
            series = self._evaluate_source(
                source,
                n_frames=n_frames,
                marker_series=marker_series,
                joint_center_series=joint_center_series,
            )
            if series is None:
                continue
            markers_used = list(source.names)
            if source.name and source.type == "joint_center":
                markers_used = [source.name]
            elif source.name and source.name not in markers_used:
                markers_used.append(source.name)
            return series, {
                "source_type": source.type,
                "source_markers": markers_used,
            }
        return None, {"source_type": None, "source_markers": []}

    def _evaluate_source(
        self,
        source: JointSourceSpec,
        *,
        n_frames: int,
        marker_series: dict[str, FloatArray],
        joint_center_series: dict[str, FloatArray],
    ) -> FloatArray | None:
        """Evaluate one YAML source into an ``(N, 3)`` series."""
        if source.type == "joint_center":
            name = source.name
            if not name or name not in joint_center_series:
                return None
            series = joint_center_series[name]
            return self._fit_series_to_frames(series, n_frames)

        if source.type in {"marker", "markers"}:
            names = list(source.names)
            if source.name and source.name not in names:
                names.append(source.name)
            available = []
            for name in names:
                if name in marker_series:
                    available.append(
                        self._fit_series_to_frames(marker_series[name], n_frames)
                    )
            if not available:
                return None
            stacked = np.stack(available, axis=0)  # (M, N, 3)
            method = (source.method or "centroid").lower()
            if method == "first":
                return available[0]
            # centroid / mean
            return np.nanmean(stacked, axis=0)

        self.log.warning("Unknown joint source type %r", source.type)
        return None

    def _fit_series_to_frames(self, series: FloatArray, n_frames: int) -> FloatArray:
        """Trim or pad a series to ``n_frames`` (pad with NaN)."""
        if series.shape[0] == n_frames:
            return series
        if series.shape[0] > n_frames:
            return series[:n_frames]
        out = np.full((n_frames, COORDINATE_DIMENSION), np.nan, dtype=float)
        out[: series.shape[0]] = series
        return out

    # -- poses / bones -----------------------------------------------------

    def _assemble_poses(
        self,
        n_frames: int,
        joint_positions: dict[str, FloatArray],
        globally_unresolved: list[str],
    ) -> list[Pose]:
        """Build one Pose per frame, preserving frame indices."""
        poses: list[Pose] = []
        joint_names = list(joint_positions.keys())
        for frame_index in range(n_frames):
            positions: dict[str, FloatArray] = {}
            missing: list[str] = []
            for joint_name in joint_names:
                xyz = joint_positions[joint_name][frame_index]
                if not np.all(np.isfinite(xyz)):
                    missing.append(joint_name)
                    continue
                positions[joint_name] = np.asarray(xyz, dtype=float).reshape(3,)
            # Include joints that never resolved at all.
            for joint_name in globally_unresolved:
                if joint_name not in missing and joint_name not in positions:
                    missing.append(joint_name)
            poses.append(
                Pose(
                    frame_index=frame_index,
                    joint_positions=positions,
                    missing_joints=sorted(set(missing)),
                )
            )
        return poses

    def _build_bones(
        self,
        n_frames: int,
        joint_positions: dict[str, FloatArray],
    ) -> dict[str, Bone]:
        """Assemble bones and compute per-frame + mean lengths."""
        bones: dict[str, Bone] = {}
        for bone_name, definition in self.definition.bones.items():
            parent = joint_positions.get(definition.parent_joint)
            child = joint_positions.get(definition.child_joint)
            lengths = np.full((n_frames,), np.nan, dtype=float)
            if parent is not None and child is not None:
                delta = child - parent
                lengths = np.linalg.norm(delta, axis=1)
            finite = lengths[np.isfinite(lengths)]
            mean_length = float(np.mean(finite)) if finite.size else None
            bones[bone_name] = Bone(
                name=bone_name,
                parent_joint=definition.parent_joint,
                child_joint=definition.child_joint,
                length=mean_length,
                lengths=lengths,
                units=UNKNOWN_UNITS,
            )
        return bones


def load_skeleton_definition(path: str | Path | None = None) -> SkeletonDefinition:
    """Convenience loader for the YAML skeleton definition."""
    return SkeletonDefinition.from_yaml(path or DEFAULT_SKELETON_DEFINITION_PATH)
