"""
Domain models for the Motion Engine.

These classes form the core SDK object graph described in
``docs/motion_database_design.md``. They represent data only: no MATLAB I/O,
no parsing, no biomechanical analysis, and no visualization.

Object graph
------------
MotionDatabase
└── Subject
       ├── Metadata
       └── Session
              ├── Kinematics
              │      ├── Marker ──────────► Trajectory
              │      ├── JointAngle ──────► Trajectory
              │      ├── JointCenter ─────► Trajectory
              │      ├── CenterOfMass ────► Trajectory
              │      └── SegmentCOM ──────► Trajectory
              └── ClinicalMetric
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from motion_engine.constants import (
    COORDINATE_DIMENSION,
    UNKNOWN_UNITS,
    VALID_SESSION_CLASSIFICATIONS,
    VALID_TRAJECTORY_LAYOUTS,
)
from motion_engine.exceptions import (
    ModelValidationError,
    SessionNotFoundError,
    SubjectNotFoundError,
    VariableNotFoundError,
)
from motion_engine.typing import (
    OpaqueValue,
    SessionClassification,
    SessionName,
    SubjectId,
    TrajectoryLayout,
    VariableName,
)

FloatArray = NDArray[np.floating[Any]]


# ---------------------------------------------------------------------------
# Validation report (lightweight; not the full validator module)
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class ValidationReport:
    """Result of lightweight structural validation on a domain object.

    Attributes:
        ok: True when ``errors`` is empty.
        errors: Hard structural problems.
        warnings: Soft inconsistencies that do not invalidate the object.
        infos: Informational notes (e.g. Unknown units).
    """

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    infos: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """Return True when there are no hard errors."""
        return not self.errors

    def extend(self, other: ValidationReport) -> None:
        """Merge another report into this one in place."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.infos.extend(other.infos)

    def raise_if_errors(self) -> None:
        """Raise :class:`ModelValidationError` if any hard errors exist."""
        if self.errors:
            message = "; ".join(self.errors)
            raise ModelValidationError(message)

    def __repr__(self) -> str:
        return (
            f"ValidationReport(ok={self.ok!r}, "
            f"errors={len(self.errors)}, "
            f"warnings={len(self.warnings)}, "
            f"infos={len(self.infos)})"
        )


# ---------------------------------------------------------------------------
# Trajectory and kinematic variables
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class Trajectory:
    """Reusable XYZ (or XYZ-like) trajectory time series.

    Attributes:
        coordinates: 2D array in either ``(N, 3)`` or ``(3, N)`` layout.
        n_frames: Number of time frames (non-coordinate dimension), or None
            when the layout could not be determined.
        layout: Detected storage layout (``"N,3"``, ``"3,N"``, or None).
        units: Physical units; defaults to ``"Unknown"``.
        coordinate_axis: Axis index of the size-3 XYZ dimension, or None.
    """

    coordinates: FloatArray
    n_frames: int | None = None
    layout: TrajectoryLayout = None
    units: str = UNKNOWN_UNITS
    coordinate_axis: int | None = None

    def __post_init__(self) -> None:
        array = np.asarray(self.coordinates)
        if array.ndim != 2:
            raise ModelValidationError(
                f"Trajectory.coordinates must be 2D, got ndim={array.ndim}"
            )
        object.__setattr__(self, "coordinates", array.astype(float, copy=False))
        self.validate().raise_if_errors()

    @property
    def shape(self) -> tuple[int, ...]:
        """Return the shape of the coordinate array."""
        return tuple(int(dim) for dim in self.coordinates.shape)

    @property
    def is_resolved(self) -> bool:
        """Return True when layout and frame count are both known."""
        return self.layout is not None and self.n_frames is not None

    def validate(self) -> ValidationReport:
        """Perform lightweight structural validation."""
        report = ValidationReport()
        if self.coordinates.ndim != 2:
            report.errors.append("coordinates must be a 2D array")
            return report

        if self.layout is not None and self.layout not in VALID_TRAJECTORY_LAYOUTS:
            report.errors.append(
                f"layout must be one of {sorted(VALID_TRAJECTORY_LAYOUTS)} or None, "
                f"got {self.layout!r}"
            )

        if self.n_frames is not None and self.n_frames < 0:
            report.errors.append(f"n_frames must be >= 0, got {self.n_frames}")

        if self.layout == "N,3":
            if self.coordinates.shape[1] != COORDINATE_DIMENSION:
                report.errors.append(
                    f"layout 'N,3' requires shape[1]={COORDINATE_DIMENSION}, "
                    f"got {self.coordinates.shape}"
                )
            elif self.n_frames is not None and self.n_frames != self.coordinates.shape[0]:
                report.errors.append(
                    f"n_frames {self.n_frames} does not match shape[0]="
                    f"{self.coordinates.shape[0]} for layout 'N,3'"
                )
        elif self.layout == "3,N":
            if self.coordinates.shape[0] != COORDINATE_DIMENSION:
                report.errors.append(
                    f"layout '3,N' requires shape[0]={COORDINATE_DIMENSION}, "
                    f"got {self.coordinates.shape}"
                )
            elif self.n_frames is not None and self.n_frames != self.coordinates.shape[1]:
                report.errors.append(
                    f"n_frames {self.n_frames} does not match shape[1]="
                    f"{self.coordinates.shape[1]} for layout '3,N'"
                )

        if self.units == UNKNOWN_UNITS:
            report.infos.append("units are Unknown")

        return report

    def __repr__(self) -> str:
        return (
            f"Trajectory(shape={self.shape}, n_frames={self.n_frames!r}, "
            f"layout={self.layout!r}, units={self.units!r})"
        )


@dataclass(slots=True)
class Marker:
    """Named marker trajectory.

    Attributes:
        name: Original marker label (e.g. ``LFHD``).
        trajectory: XYZ trajectory data.
        coordinate_system: Lab / anatomic frame if known; otherwise None.
    """

    name: VariableName
    trajectory: Trajectory
    coordinate_system: str | None = None

    def __post_init__(self) -> None:
        self.validate().raise_if_errors()

    @property
    def n_frames(self) -> int | None:
        """Return the trajectory frame count."""
        return self.trajectory.n_frames

    @property
    def units(self) -> str:
        """Return trajectory units."""
        return self.trajectory.units

    def validate(self) -> ValidationReport:
        """Validate marker name and nested trajectory."""
        report = ValidationReport()
        if not self.name:
            report.errors.append("Marker.name must be a non-empty string")
        report.extend(self.trajectory.validate())
        if self.coordinate_system is None:
            report.infos.append("coordinate_system is unset")
        return report

    def __repr__(self) -> str:
        return (
            f"Marker(name={self.name!r}, n_frames={self.n_frames!r}, "
            f"units={self.units!r})"
        )


@dataclass(slots=True)
class JointAngle:
    """Named joint-angle time series.

    Attributes:
        name: Original angle label (e.g. ``LKneeAngles``).
        trajectory: Underlying time-series array (typically XYZ-like axes).
        rotation_axes: Optional axis semantics; None when unspecified.
    """

    name: VariableName
    trajectory: Trajectory
    rotation_axes: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        self.validate().raise_if_errors()

    @property
    def series(self) -> FloatArray:
        """Return the underlying coordinate / series array."""
        return self.trajectory.coordinates

    @property
    def n_frames(self) -> int | None:
        """Return the series frame count."""
        return self.trajectory.n_frames

    @property
    def units(self) -> str:
        """Return series units."""
        return self.trajectory.units

    def validate(self) -> ValidationReport:
        """Validate joint-angle name and nested trajectory."""
        report = ValidationReport()
        if not self.name:
            report.errors.append("JointAngle.name must be a non-empty string")
        report.extend(self.trajectory.validate())
        if self.rotation_axes is None:
            report.infos.append("rotation_axes are unspecified")
        return report

    def __repr__(self) -> str:
        return (
            f"JointAngle(name={self.name!r}, n_frames={self.n_frames!r}, "
            f"units={self.units!r})"
        )


@dataclass(slots=True)
class JointCenter:
    """Named joint-center position trajectory.

    Attributes:
        name: Original label (e.g. ``LHJC``).
        trajectory: XYZ trajectory data.
    """

    name: VariableName
    trajectory: Trajectory

    def __post_init__(self) -> None:
        self.validate().raise_if_errors()

    @property
    def n_frames(self) -> int | None:
        """Return the trajectory frame count."""
        return self.trajectory.n_frames

    @property
    def units(self) -> str:
        """Return trajectory units."""
        return self.trajectory.units

    def validate(self) -> ValidationReport:
        """Validate joint-center name and nested trajectory."""
        report = ValidationReport()
        if not self.name:
            report.errors.append("JointCenter.name must be a non-empty string")
        report.extend(self.trajectory.validate())
        return report

    def __repr__(self) -> str:
        return (
            f"JointCenter(name={self.name!r}, n_frames={self.n_frames!r}, "
            f"units={self.units!r})"
        )


@dataclass(slots=True)
class CenterOfMass:
    """Whole-body center-of-mass trajectory.

    Attributes:
        name: Original label (e.g. ``CentreOfMass``).
        trajectory: XYZ trajectory data.
    """

    name: VariableName
    trajectory: Trajectory

    def __post_init__(self) -> None:
        self.validate().raise_if_errors()

    @property
    def n_frames(self) -> int | None:
        """Return the trajectory frame count."""
        return self.trajectory.n_frames

    @property
    def units(self) -> str:
        """Return trajectory units."""
        return self.trajectory.units

    def validate(self) -> ValidationReport:
        """Validate COM name and nested trajectory."""
        report = ValidationReport()
        if not self.name:
            report.errors.append("CenterOfMass.name must be a non-empty string")
        report.extend(self.trajectory.validate())
        return report

    def __repr__(self) -> str:
        return (
            f"CenterOfMass(name={self.name!r}, n_frames={self.n_frames!r}, "
            f"units={self.units!r})"
        )


@dataclass(slots=True)
class SegmentCOM:
    """Segment-level center-of-mass trajectory.

    Attributes:
        name: Original label (e.g. ``PelvisCOM``).
        trajectory: XYZ trajectory data.
    """

    name: VariableName
    trajectory: Trajectory

    def __post_init__(self) -> None:
        self.validate().raise_if_errors()

    @property
    def n_frames(self) -> int | None:
        """Return the trajectory frame count."""
        return self.trajectory.n_frames

    @property
    def units(self) -> str:
        """Return trajectory units."""
        return self.trajectory.units

    def validate(self) -> ValidationReport:
        """Validate segment COM name and nested trajectory."""
        report = ValidationReport()
        if not self.name:
            report.errors.append("SegmentCOM.name must be a non-empty string")
        report.extend(self.trajectory.validate())
        return report

    def __repr__(self) -> str:
        return (
            f"SegmentCOM(name={self.name!r}, n_frames={self.n_frames!r}, "
            f"units={self.units!r})"
        )


@dataclass(slots=True)
class ClinicalMetric:
    """Scalar or structured clinical result (not a trajectory).

    Attributes:
        name: Original metric label (e.g. ``StpLen``).
        value: Extracted value (scalar, array, or opaque MATLAB content).
        description: Optional human description; None until supplied.
        units: Physical units; defaults to ``"Unknown"``.
    """

    name: VariableName
    value: OpaqueValue
    description: str | None = None
    units: str = UNKNOWN_UNITS

    def __post_init__(self) -> None:
        self.validate().raise_if_errors()

    def validate(self) -> ValidationReport:
        """Validate clinical metric name and unit policy note."""
        report = ValidationReport()
        if not self.name:
            report.errors.append("ClinicalMetric.name must be a non-empty string")
        if self.units == UNKNOWN_UNITS:
            report.infos.append("units are Unknown")
        if self.description is None:
            report.infos.append("description is unset")
        return report

    def __repr__(self) -> str:
        return (
            f"ClinicalMetric(name={self.name!r}, units={self.units!r}, "
            f"description={self.description!r})"
        )


# ---------------------------------------------------------------------------
# Metadata, kinematics, session, subject, database
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class Metadata:
    """Subject-level metadata from ``Subject.Info``.

    Opaque MATLAB objects (e.g. reference posture tables) are retained without
    reinterpretation.
    """

    first_frame: int | None = None
    last_frame: int | None = None
    vrate: float | None = None
    fprate: float | None = None
    mass: float | None = None
    height: float | None = None
    lleg_length: float | None = None
    rleg_length: float | None = None
    ref_th_posture: OpaqueValue | None = None
    ref_hd_posture: OpaqueValue | None = None
    extras: dict[str, OpaqueValue] = field(default_factory=dict)

    def to_dict(self) -> dict[str, OpaqueValue]:
        """Return a plain dictionary of known metadata fields plus extras."""
        data: dict[str, OpaqueValue] = {
            "FirstFrame": self.first_frame,
            "LastFrame": self.last_frame,
            "Vrate": self.vrate,
            "FPrate": self.fprate,
            "Mass": self.mass,
            "Height": self.height,
            "LLegLength": self.lleg_length,
            "RLegLength": self.rleg_length,
            "RefThPosture": self.ref_th_posture,
            "RefHdPosture": self.ref_hd_posture,
        }
        data.update(self.extras)
        return data

    def validate(self) -> ValidationReport:
        """Validate numeric metadata when present."""
        report = ValidationReport()
        for label, value in (
            ("vrate", self.vrate),
            ("fprate", self.fprate),
            ("mass", self.mass),
            ("height", self.height),
            ("lleg_length", self.lleg_length),
            ("rleg_length", self.rleg_length),
        ):
            if value is not None and value < 0:
                report.errors.append(f"Metadata.{label} must be >= 0, got {value}")
        if (
            self.first_frame is not None
            and self.last_frame is not None
            and self.last_frame < self.first_frame
        ):
            report.errors.append(
                "Metadata.last_frame must be >= first_frame "
                f"({self.last_frame} < {self.first_frame})"
            )
        return report

    def __repr__(self) -> str:
        return (
            f"Metadata(vrate={self.vrate!r}, fprate={self.fprate!r}, "
            f"mass={self.mass!r}, height={self.height!r})"
        )


@dataclass(slots=True)
class Kinematics:
    """Session kinematics container.

    Owns all trajectory-backed kinematic variable families for one session.
    """

    markers: dict[VariableName, Marker] = field(default_factory=dict)
    joint_angles: dict[VariableName, JointAngle] = field(default_factory=dict)
    joint_centers: dict[VariableName, JointCenter] = field(default_factory=dict)
    com: dict[VariableName, CenterOfMass] = field(default_factory=dict)
    segment_com: dict[VariableName, SegmentCOM] = field(default_factory=dict)

    def list_markers(self) -> list[VariableName]:
        """Return sorted marker names."""
        return sorted(self.markers)

    def get_marker(self, name: VariableName) -> Marker:
        """Return a marker by original name."""
        try:
            return self.markers[name]
        except KeyError as exc:
            raise VariableNotFoundError(f"Marker not found: {name!r}") from exc

    def list_joint_angles(self) -> list[VariableName]:
        """Return sorted joint-angle names."""
        return sorted(self.joint_angles)

    def get_joint_angle(self, name: VariableName) -> JointAngle:
        """Return a joint angle by original name."""
        try:
            return self.joint_angles[name]
        except KeyError as exc:
            raise VariableNotFoundError(f"JointAngle not found: {name!r}") from exc

    def variable_counts(self) -> dict[str, int]:
        """Return counts by kinematic category."""
        return {
            "markers": len(self.markers),
            "joint_angles": len(self.joint_angles),
            "joint_centers": len(self.joint_centers),
            "com": len(self.com),
            "segment_com": len(self.segment_com),
        }

    def validate(self) -> ValidationReport:
        """Validate all nested kinematic variables."""
        report = ValidationReport()
        for collection in (
            self.markers,
            self.joint_angles,
            self.joint_centers,
            self.com,
            self.segment_com,
        ):
            for key, variable in collection.items():
                if key != variable.name:
                    report.errors.append(
                        f"Kinematics key {key!r} does not match "
                        f"variable.name {variable.name!r}"
                    )
                report.extend(variable.validate())
        return report

    def __repr__(self) -> str:
        counts = self.variable_counts()
        return (
            "Kinematics("
            f"markers={counts['markers']}, "
            f"joint_angles={counts['joint_angles']}, "
            f"joint_centers={counts['joint_centers']}, "
            f"com={counts['com']}, "
            f"segment_com={counts['segment_com']})"
        )


@dataclass(slots=True)
class Session:
    """One capture session belonging to a subject.

    Attributes:
        name: Original session name (preserved exactly).
        subject_id: Owning subject ID.
        classification: Semantic label only (not a rename).
        frame_count: Layout-aware frame count, or None if unresolved.
        trajectory_layout: Dominant / session-level layout hint.
        sampling_rate_hz: Mocap sampling rate applicable to kinematics.
        kinematics: Trajectory-backed kinematic variables.
        clinical_metrics: Clinical results from session ``Res``.
    """

    name: SessionName
    subject_id: SubjectId
    classification: SessionClassification = "Unknown"
    frame_count: int | None = None
    trajectory_layout: TrajectoryLayout = None
    sampling_rate_hz: float | None = None
    kinematics: Kinematics = field(default_factory=Kinematics)
    clinical_metrics: dict[VariableName, ClinicalMetric] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.validate().raise_if_errors()

    def list_metrics(self) -> list[VariableName]:
        """Return sorted clinical metric names."""
        return sorted(self.clinical_metrics)

    def get_metric(self, name: VariableName) -> ClinicalMetric:
        """Return a clinical metric by original name."""
        try:
            return self.clinical_metrics[name]
        except KeyError as exc:
            raise VariableNotFoundError(
                f"ClinicalMetric not found: {name!r}"
            ) from exc

    def validate(self) -> ValidationReport:
        """Validate session identity, classification, and nested data."""
        report = ValidationReport()
        if not self.name:
            report.errors.append("Session.name must be a non-empty string")
        if not self.subject_id:
            report.errors.append("Session.subject_id must be a non-empty string")
        if self.classification not in VALID_SESSION_CLASSIFICATIONS:
            report.errors.append(
                f"Unsupported session classification: {self.classification!r}"
            )
        if self.frame_count is not None and self.frame_count < 0:
            report.errors.append(
                f"Session.frame_count must be >= 0, got {self.frame_count}"
            )
        if self.sampling_rate_hz is not None and self.sampling_rate_hz <= 0:
            report.errors.append(
                f"Session.sampling_rate_hz must be > 0, got {self.sampling_rate_hz}"
            )
        if (
            self.trajectory_layout is not None
            and self.trajectory_layout not in VALID_TRAJECTORY_LAYOUTS
        ):
            report.errors.append(
                f"Unsupported trajectory_layout: {self.trajectory_layout!r}"
            )
        report.extend(self.kinematics.validate())
        for key, metric in self.clinical_metrics.items():
            if key != metric.name:
                report.errors.append(
                    f"Clinical metric key {key!r} does not match "
                    f"metric.name {metric.name!r}"
                )
            report.extend(metric.validate())
        return report

    def __repr__(self) -> str:
        return (
            f"Session(name={self.name!r}, subject_id={self.subject_id!r}, "
            f"classification={self.classification!r}, "
            f"frame_count={self.frame_count!r})"
        )


@dataclass(slots=True)
class Subject:
    """One participant entry in the motion database.

    Attributes:
        id: Stable subject ID (e.g. ``S2``).
        metadata: Subject-level ``Info`` fields.
        sessions: Mapping of original session name → :class:`Session`.
    """

    id: SubjectId
    metadata: Metadata = field(default_factory=Metadata)
    sessions: dict[SessionName, Session] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.validate().raise_if_errors()

    def list_sessions(self) -> list[SessionName]:
        """Return sorted original session names."""
        return sorted(self.sessions)

    def get_session(self, name: SessionName) -> Session:
        """Return a session by original name."""
        try:
            return self.sessions[name]
        except KeyError as exc:
            raise SessionNotFoundError(
                f"Session {name!r} not found for subject {self.id!r}"
            ) from exc

    def has_session(self, name: SessionName) -> bool:
        """Return True if the session name exists."""
        return name in self.sessions

    def sessions_by_class(self, classification: SessionClassification) -> list[Session]:
        """Return sessions matching a semantic classification label."""
        return [
            session
            for session in self.sessions.values()
            if session.classification == classification
        ]

    def add_session(self, session: Session) -> None:
        """Attach a session, enforcing subject ID consistency."""
        if session.subject_id != self.id:
            raise ModelValidationError(
                f"Session.subject_id {session.subject_id!r} does not match "
                f"Subject.id {self.id!r}"
            )
        self.sessions[session.name] = session

    def summary(self) -> dict[str, Any]:
        """Return a lightweight summary dictionary for inspection."""
        class_counts: dict[str, int] = {}
        frame_counts = [
            session.frame_count
            for session in self.sessions.values()
            if session.frame_count is not None
        ]
        for session in self.sessions.values():
            class_counts[session.classification] = (
                class_counts.get(session.classification, 0) + 1
            )
        return {
            "subject_id": self.id,
            "session_count": len(self.sessions),
            "classifications": class_counts,
            "frame_count_min": min(frame_counts) if frame_counts else None,
            "frame_count_max": max(frame_counts) if frame_counts else None,
            "metadata": {
                "vrate": self.metadata.vrate,
                "fprate": self.metadata.fprate,
                "mass": self.metadata.mass,
                "height": self.metadata.height,
            },
        }

    def validate(self) -> ValidationReport:
        """Validate subject identity and nested sessions/metadata."""
        report = ValidationReport()
        if not self.id:
            report.errors.append("Subject.id must be a non-empty string")
        report.extend(self.metadata.validate())
        for key, session in self.sessions.items():
            if key != session.name:
                report.errors.append(
                    f"Session key {key!r} does not match session.name {session.name!r}"
                )
            if session.subject_id != self.id:
                report.errors.append(
                    f"Session {session.name!r} subject_id {session.subject_id!r} "
                    f"does not match Subject.id {self.id!r}"
                )
            report.extend(session.validate())
        return report

    def __repr__(self) -> str:
        return f"Subject(id={self.id!r}, sessions={len(self.sessions)})"


@dataclass(slots=True)
class MotionDatabase:
    """In-memory motion database owning all subjects.

    This class is the SDK root object. It does **not** load MATLAB files;
    population is performed by future loader/parser modules (or by tests /
    constructors attaching :class:`Subject` instances).
    """

    subjects: dict[SubjectId, Subject] = field(default_factory=dict)
    dataset_path: Path | None = None
    catalog_path: Path | None = None

    def list_subjects(self) -> list[SubjectId]:
        """Return sorted subject IDs."""
        return sorted(self.subjects)

    def has_subject(self, subject_id: SubjectId) -> bool:
        """Return True if the subject ID exists."""
        return subject_id in self.subjects

    def get_subject(self, subject_id: SubjectId) -> Subject:
        """Return a subject by ID."""
        try:
            return self.subjects[subject_id]
        except KeyError as exc:
            raise SubjectNotFoundError(
                f"Subject not found: {subject_id!r}"
            ) from exc

    def iter_subjects(self) -> Iterator[Subject]:
        """Iterate subjects in sorted ID order."""
        for subject_id in self.list_subjects():
            yield self.subjects[subject_id]

    def add_subject(self, subject: Subject) -> None:
        """Attach a subject to the database."""
        report = subject.validate()
        report.raise_if_errors()
        self.subjects[subject.id] = subject

    def __len__(self) -> int:
        """Return the number of subjects."""
        return len(self.subjects)

    def __contains__(self, subject_id: object) -> bool:
        """Support ``subject_id in database`` checks."""
        return isinstance(subject_id, str) and subject_id in self.subjects

    def load(self, path: str | Path | None = None) -> MotionDatabase:
        """Load a MATLAB dataset into this database.

        Not implemented in the architecture phase.

        Raises:
            NotImplementedError: Always; see ``motion_engine.loader``.
        """
        raise NotImplementedError(
            "MotionDatabase.load() is intentionally unimplemented. "
            "MATLAB loading belongs in motion_engine.loader / parser."
        )

    def validate(self) -> ValidationReport:
        """Run lightweight structural validation across all subjects."""
        report = ValidationReport()
        if not self.subjects:
            report.warnings.append("MotionDatabase contains no subjects")
        for subject_id, subject in self.subjects.items():
            if subject_id != subject.id:
                report.errors.append(
                    f"Subject key {subject_id!r} does not match "
                    f"subject.id {subject.id!r}"
                )
            report.extend(subject.validate())
        return report

    def statistics(self) -> Mapping[str, Any]:
        """Return aggregate statistics.

        Not implemented in the architecture phase.

        Raises:
            NotImplementedError: Always; see ``motion_engine.statistics``.
        """
        raise NotImplementedError(
            "MotionDatabase.statistics() belongs in motion_engine.statistics."
        )

    def session_types(self) -> list[dict[str, Any]]:
        """Return semantic session-type summary records.

        Lightweight architecture helper: aggregates classification counts from
        currently attached subjects. Full catalog-backed reporting remains in
        the statistics module.
        """
        rows: dict[str, dict[str, Any]] = {}
        for subject in self.iter_subjects():
            for session in subject.sessions.values():
                row = rows.setdefault(
                    session.name,
                    {
                        "original_name": session.name,
                        "classification": session.classification,
                        "frequency": 0,
                        "subjects_present": [],
                    },
                )
                row["frequency"] += 1
                row["subjects_present"].append(subject.id)
        for row in rows.values():
            row["subjects_present"] = sorted(set(row["subjects_present"]))
        return [rows[name] for name in sorted(rows)]

    def units_policy(self) -> dict[str, Any]:
        """Return the default units policy for the domain model."""
        return {
            "default_units": UNKNOWN_UNITS,
            "policy": (
                "Never guess units. Record Unknown unless an authoritative "
                "source specifies otherwise."
            ),
            "categories": [
                "markers",
                "joint_angles",
                "joint_centers",
                "com",
                "segment_com",
                "clinical_metrics",
            ],
        }

    def __repr__(self) -> str:
        return (
            f"MotionDatabase(subjects={len(self.subjects)}, "
            f"dataset_path={self.dataset_path!r})"
        )
