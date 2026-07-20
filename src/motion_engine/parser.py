"""
MATLAB → MotionDatabase parser for the Motion Engine.

This module is a translator only. It converts nested MATLAB structures into
the domain model defined in :mod:`motion_engine.models` without modifying the
dataset, renaming variables/sessions, or performing biomechanical analysis.
"""

from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from motion_engine.constants import UNKNOWN_UNITS
from motion_engine.exceptions import ModelValidationError, ParserError
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
)
from motion_engine.typing import SessionName, SubjectId, TrajectoryLayout, VariableName
from motion_engine.utils import (
    GLOBAL_DAT_SKIP_FIELDS,
    SESSION_CONTAINER_SKIP_FIELDS,
    categorize_kinematic_variable,
    classify_session_name,
    detect_trajectory_layout,
    load_catalog_session_classifications,
    matlab_scalar,
    unwrap_matlab,
)

logger = logging.getLogger(__name__)

FloatArray = NDArray[np.floating[Any]]


# ---------------------------------------------------------------------------
# Trajectory builders
# ---------------------------------------------------------------------------


def build_trajectory(
    array: Any,
    *,
    context: str = "",
    log: logging.Logger | None = None,
) -> Trajectory | None:
    """Build a :class:`Trajectory` from a MATLAB kinematics array.

    Reuses the array buffer when possible. Returns None when the value is not
    a 2D numeric array suitable for layout detection.
    """
    log = log or logger
    data = unwrap_matlab(array)
    if not isinstance(data, np.ndarray):
        log.warning("%s: expected ndarray trajectory, got %s", context, type(data))
        return None
    if data.dtype == object:
        log.warning("%s: object-dtype array is not a numeric trajectory", context)
        return None
    if data.ndim != 2:
        log.warning("%s: expected 2D trajectory, got shape %s", context, data.shape)
        return None

    # Prefer a view / same buffer; astype(copy=False) happens inside Trajectory.
    numeric = np.asarray(data)
    try:
        layout_info = detect_trajectory_layout(numeric, context=context, log=log)
    except ValueError as exc:
        log.warning("%s: layout detection failed: %s", context, exc)
        return None

    layout: TrajectoryLayout = layout_info["layout"]
    if layout is None:
        log.warning("%s: unresolved trajectory layout for shape %s", context, numeric.shape)

    return Trajectory(
        coordinates=numeric,
        n_frames=layout_info["frame_count"],
        layout=layout,
        units=UNKNOWN_UNITS,
        coordinate_axis=layout_info["coordinate_axis"],
    )


# ---------------------------------------------------------------------------
# Metadata / clinical metrics
# ---------------------------------------------------------------------------


_METADATA_FIELD_MAP: dict[str, str] = {
    "FirstFrame": "first_frame",
    "LastFrame": "last_frame",
    "Vrate": "vrate",
    "FPrate": "fprate",
    "Mass": "mass",
    "Height": "height",
    "LLegLength": "lleg_length",
    "RLegLength": "rleg_length",
    "RefThPosture": "ref_th_posture",
    "RefHdPosture": "ref_hd_posture",
}


def parse_metadata(
    subject_struct: Any,
    *,
    subject_id: SubjectId,
    log: logging.Logger | None = None,
) -> Metadata:
    """Parse ``Subject.Info`` into :class:`Metadata`.

    Known fields are mapped onto typed attributes. Unknown fields are preserved
    in ``Metadata.extras``.
    """
    log = log or logger
    if not hasattr(subject_struct, "dtype") or subject_struct.dtype.names is None:
        log.warning("Subject %s: corrupted hierarchy (no struct fields)", subject_id)
        raise ParserError(f"Subject {subject_id!r} has a corrupted hierarchy")

    if "Info" not in subject_struct.dtype.names:
        log.warning("Subject %s: missing Info metadata", subject_id)
        return Metadata()

    info = unwrap_matlab(subject_struct["Info"])
    if not hasattr(info, "dtype") or info.dtype.names is None:
        log.warning("Subject %s: Info is not a struct; metadata empty", subject_id)
        return Metadata()

    kwargs: dict[str, Any] = {}
    extras: dict[str, Any] = {}
    opaque_fields = {"ref_th_posture", "ref_hd_posture"}

    for field_name in info.dtype.names:
        raw = info[field_name]
        value = unwrap_matlab(raw)
        attr = _METADATA_FIELD_MAP.get(field_name)
        if attr is None:
            extras[field_name] = value
            continue
        if attr in opaque_fields:
            kwargs[attr] = value
        else:
            kwargs[attr] = matlab_scalar(value)

    if extras:
        kwargs["extras"] = extras
        log.debug(
            "Subject %s: preserved %d unknown metadata field(s)",
            subject_id,
            len(extras),
        )

    return Metadata(**kwargs)


def parse_clinical_metrics(
    session_struct: Any,
    *,
    context: str = "",
    log: logging.Logger | None = None,
) -> dict[VariableName, ClinicalMetric]:
    """Parse ``session.Res`` into clinical metrics (not gait events)."""
    log = log or logger
    metrics: dict[VariableName, ClinicalMetric] = {}

    if not hasattr(session_struct, "dtype") or session_struct.dtype.names is None:
        return metrics
    if "Res" not in session_struct.dtype.names:
        return metrics

    res = unwrap_matlab(session_struct["Res"])
    if not hasattr(res, "dtype") or res.dtype.names is None:
        log.warning("%s: Res present but not a struct; skipping metrics", context)
        return metrics

    for name in res.dtype.names:
        try:
            value = unwrap_matlab(res[name])
            metrics[name] = ClinicalMetric(
                name=name,
                value=value,
                description=None,
                units=UNKNOWN_UNITS,
            )
        except ModelValidationError as exc:
            log.warning("%s: skipped clinical metric %s (%s)", context, name, exc)
        except Exception as exc:  # noqa: BLE001 - keep parsing
            log.warning("%s: failed clinical metric %s: %s", context, name, exc)

    return metrics


# ---------------------------------------------------------------------------
# Kinematics families
# ---------------------------------------------------------------------------


def parse_markers(
    kinematics_struct: Any,
    field_names: list[str],
    *,
    context: str,
    log: logging.Logger | None = None,
) -> dict[VariableName, Marker]:
    """Parse marker trajectories from a kinematics struct."""
    log = log or logger
    markers: dict[VariableName, Marker] = {}
    for name in field_names:
        traj = build_trajectory(
            kinematics_struct[name],
            context=f"{context}/{name}",
            log=log,
        )
        if traj is None:
            log.warning("%s: missing/unreadable marker %s", context, name)
            continue
        try:
            markers[name] = Marker(name=name, trajectory=traj, coordinate_system=None)
        except ModelValidationError as exc:
            log.warning("%s: skipped marker %s (%s)", context, name, exc)
    return markers


def parse_joint_angles(
    kinematics_struct: Any,
    field_names: list[str],
    *,
    context: str,
    log: logging.Logger | None = None,
) -> dict[VariableName, JointAngle]:
    """Parse joint-angle time series from a kinematics struct."""
    log = log or logger
    angles: dict[VariableName, JointAngle] = {}
    for name in field_names:
        traj = build_trajectory(
            kinematics_struct[name],
            context=f"{context}/{name}",
            log=log,
        )
        if traj is None:
            log.warning("%s: missing/unreadable joint angle %s", context, name)
            continue
        try:
            angles[name] = JointAngle(
                name=name,
                trajectory=traj,
                rotation_axes=None,
            )
        except ModelValidationError as exc:
            log.warning("%s: skipped joint angle %s (%s)", context, name, exc)
    return angles


def parse_joint_centers(
    kinematics_struct: Any,
    field_names: list[str],
    *,
    context: str,
    log: logging.Logger | None = None,
) -> dict[VariableName, JointCenter]:
    """Parse joint-center trajectories from a kinematics struct."""
    log = log or logger
    centers: dict[VariableName, JointCenter] = {}
    for name in field_names:
        traj = build_trajectory(
            kinematics_struct[name],
            context=f"{context}/{name}",
            log=log,
        )
        if traj is None:
            log.warning("%s: missing/unreadable joint center %s", context, name)
            continue
        try:
            centers[name] = JointCenter(name=name, trajectory=traj)
        except ModelValidationError as exc:
            log.warning("%s: skipped joint center %s (%s)", context, name, exc)
    return centers


def parse_center_of_mass(
    kinematics_struct: Any,
    field_names: list[str],
    *,
    context: str,
    log: logging.Logger | None = None,
) -> dict[VariableName, CenterOfMass]:
    """Parse whole-body COM trajectories from a kinematics struct."""
    log = log or logger
    com: dict[VariableName, CenterOfMass] = {}
    for name in field_names:
        traj = build_trajectory(
            kinematics_struct[name],
            context=f"{context}/{name}",
            log=log,
        )
        if traj is None:
            log.warning("%s: missing/unreadable COM %s", context, name)
            continue
        try:
            com[name] = CenterOfMass(name=name, trajectory=traj)
        except ModelValidationError as exc:
            log.warning("%s: skipped COM %s (%s)", context, name, exc)
    return com


def parse_segment_com(
    kinematics_struct: Any,
    field_names: list[str],
    *,
    context: str,
    log: logging.Logger | None = None,
) -> dict[VariableName, SegmentCOM]:
    """Parse segment COM trajectories from a kinematics struct."""
    log = log or logger
    segments: dict[VariableName, SegmentCOM] = {}
    for name in field_names:
        traj = build_trajectory(
            kinematics_struct[name],
            context=f"{context}/{name}",
            log=log,
        )
        if traj is None:
            log.warning("%s: missing/unreadable segment COM %s", context, name)
            continue
        try:
            segments[name] = SegmentCOM(name=name, trajectory=traj)
        except ModelValidationError as exc:
            log.warning("%s: skipped segment COM %s (%s)", context, name, exc)
    return segments


def parse_kinematics(
    session_struct: Any,
    *,
    context: str,
    log: logging.Logger | None = None,
) -> Kinematics:
    """Parse ``session.kinematics`` into a :class:`Kinematics` container.

    Iterates kinematics fields once, categorizes each name, then builds the
    appropriate variable family.
    """
    log = log or logger
    empty = Kinematics()

    if not hasattr(session_struct, "dtype") or session_struct.dtype.names is None:
        log.warning("%s: session struct corrupted; empty kinematics", context)
        return empty
    if "kinematics" not in session_struct.dtype.names:
        log.warning("%s: missing kinematics section", context)
        return empty

    kin = unwrap_matlab(session_struct["kinematics"])
    if not hasattr(kin, "dtype") or kin.dtype.names is None:
        log.warning("%s: kinematics is not a struct", context)
        return empty

    buckets: dict[str, list[str]] = {
        "markers": [],
        "joint_angles": [],
        "joint_centers": [],
        "center_of_mass": [],
        "segment_com": [],
        "unknown": [],
    }
    for name in kin.dtype.names:
        buckets[categorize_kinematic_variable(name)].append(name)

    for unknown_name in buckets["unknown"]:
        log.warning("%s: unknown kinematic variable %s (skipped)", context, unknown_name)

    return Kinematics(
        markers=parse_markers(kin, buckets["markers"], context=context, log=log),
        joint_angles=parse_joint_angles(
            kin, buckets["joint_angles"], context=context, log=log
        ),
        joint_centers=parse_joint_centers(
            kin, buckets["joint_centers"], context=context, log=log
        ),
        com=parse_center_of_mass(
            kin, buckets["center_of_mass"], context=context, log=log
        ),
        segment_com=parse_segment_com(
            kin, buckets["segment_com"], context=context, log=log
        ),
    )


def _session_frame_summary(
    kinematics: Kinematics,
) -> tuple[int | None, TrajectoryLayout]:
    """Infer session frame count / layout from the first resolved marker."""
    for marker in kinematics.markers.values():
        if marker.trajectory.is_resolved:
            return marker.trajectory.n_frames, marker.trajectory.layout
    for collection in (
        kinematics.joint_angles,
        kinematics.joint_centers,
        kinematics.com,
        kinematics.segment_com,
    ):
        for variable in collection.values():
            if variable.trajectory.is_resolved:
                return variable.trajectory.n_frames, variable.trajectory.layout
    return None, None


# ---------------------------------------------------------------------------
# Session / subject / database
# ---------------------------------------------------------------------------


def parse_session(
    session_struct: Any,
    *,
    session_name: SessionName,
    subject_id: SubjectId,
    sampling_rate_hz: float | None,
    classification_lookup: dict[str, str] | None = None,
    log: logging.Logger | None = None,
) -> Session | None:
    """Parse one ``New_Session`` entry into a :class:`Session`.

    Incomplete sessions produce warnings and may return None instead of
    aborting the entire subject.
    """
    log = log or logger
    context = f"{subject_id}/{session_name}"
    log.info("Parsing session %s", context)

    try:
        kinematics = parse_kinematics(session_struct, context=context, log=log)
        clinical_metrics = parse_clinical_metrics(
            session_struct, context=context, log=log
        )
        frame_count, layout = _session_frame_summary(kinematics)
        if frame_count is None:
            log.warning("%s: unresolved session frame count", context)

        if classification_lookup and session_name in classification_lookup:
            classification = classification_lookup[session_name]
        else:
            classification = classify_session_name(session_name)

        if not kinematics.markers:
            log.warning("%s: no markers parsed", context)

        return Session(
            name=session_name,
            subject_id=subject_id,
            classification=classification,
            frame_count=frame_count,
            trajectory_layout=layout,
            sampling_rate_hz=sampling_rate_hz,
            kinematics=kinematics,
            clinical_metrics=clinical_metrics,
        )
    except ModelValidationError as exc:
        log.warning("%s: session validation failed (%s); skipping", context, exc)
        return None
    except ParserError:
        raise
    except Exception as exc:  # noqa: BLE001 - keep parsing other sessions
        log.warning("%s: unexpected session parse failure (%s); skipping", context, exc)
        return None


def parse_sessions(
    subject_struct: Any,
    *,
    subject_id: SubjectId,
    sampling_rate_hz: float | None,
    classification_lookup: dict[str, str] | None = None,
    log: logging.Logger | None = None,
) -> dict[SessionName, Session]:
    """Parse all sessions under ``subject.New_Session`` dynamically."""
    log = log or logger
    sessions: dict[SessionName, Session] = {}

    if not hasattr(subject_struct, "dtype") or subject_struct.dtype.names is None:
        raise ParserError(f"Subject {subject_id!r} has a corrupted hierarchy")

    if "New_Session" not in subject_struct.dtype.names:
        log.warning("Subject %s: missing New_Session", subject_id)
        return sessions

    container = unwrap_matlab(subject_struct["New_Session"])
    if not hasattr(container, "dtype") or container.dtype.names is None:
        log.warning("Subject %s: New_Session is not a struct", subject_id)
        return sessions

    for session_name in container.dtype.names:
        if session_name in SESSION_CONTAINER_SKIP_FIELDS:
            continue
        session_struct = unwrap_matlab(container[session_name])
        session = parse_session(
            session_struct,
            session_name=session_name,
            subject_id=subject_id,
            sampling_rate_hz=sampling_rate_hz,
            classification_lookup=classification_lookup,
            log=log,
        )
        if session is not None:
            sessions[session_name] = session

    return sessions


def parse_subject(
    subject_struct: Any,
    *,
    subject_id: SubjectId,
    classification_lookup: dict[str, str] | None = None,
    log: logging.Logger | None = None,
) -> Subject:
    """Parse one Dat subject field into a :class:`Subject`."""
    log = log or logger
    log.info("Parsing subject %s", subject_id)

    subject_struct = unwrap_matlab(subject_struct)
    if not hasattr(subject_struct, "dtype") or subject_struct.dtype.names is None:
        raise ParserError(f"Subject {subject_id!r} has a corrupted hierarchy")

    metadata = parse_metadata(subject_struct, subject_id=subject_id, log=log)
    sessions = parse_sessions(
        subject_struct,
        subject_id=subject_id,
        sampling_rate_hz=metadata.vrate,
        classification_lookup=classification_lookup,
        log=log,
    )

    try:
        subject = Subject(id=subject_id, metadata=metadata, sessions=sessions)
    except ModelValidationError as exc:
        # Soften non-fatal issues by retrying without failing sessions if needed.
        log.warning(
            "Subject %s: validation failed (%s); attempting recovery",
            subject_id,
            exc,
        )
        # Drop sessions that independently fail validation.
        recovered: dict[SessionName, Session] = {}
        for name, session in sessions.items():
            try:
                report = session.validate()
                report.raise_if_errors()
                recovered[name] = session
            except ModelValidationError as session_exc:
                log.warning(
                    "Subject %s: dropping session %s after validation (%s)",
                    subject_id,
                    name,
                    session_exc,
                )
        subject = Subject(id=subject_id, metadata=metadata, sessions=recovered)

    log.info(
        "Finished subject %s (%d session(s))",
        subject_id,
        len(subject.sessions),
    )
    return subject


def parse_database(
    mat_data: dict[str, Any],
    *,
    dataset_path: str | Path | None = None,
    catalog_path: str | Path | None = None,
    log: logging.Logger | None = None,
) -> MotionDatabase:
    """Parse a loaded MATLAB dictionary into a :class:`MotionDatabase`.

    Args:
        mat_data: Result of ``scipy.io.loadmat`` (or equivalent).
        dataset_path: Optional path recorded on the database object.
        catalog_path: Optional Motion Catalog directory for session labels.
        log: Optional logger.

    Raises:
        ParserError: When ``Dat`` is missing or the hierarchy is corrupted.
    """
    log = log or logger
    log.info("Loading database into MotionDatabase object model")

    if not isinstance(mat_data, dict):
        raise ParserError("MATLAB data must be a dictionary from loadmat()")
    if "Dat" not in mat_data:
        raise ParserError("Dataset missing top-level 'Dat' field")

    dat = mat_data["Dat"]
    if not hasattr(dat, "dtype") or dat.dtype.names is None:
        raise ParserError("Dat is missing or is not a MATLAB struct")

    classification_lookup = load_catalog_session_classifications(catalog_path)
    if classification_lookup:
        log.info(
            "Using %d session classification(s) from Motion Catalog",
            len(classification_lookup),
        )

    database = MotionDatabase(
        dataset_path=Path(dataset_path) if dataset_path is not None else None,
        catalog_path=Path(catalog_path) if catalog_path is not None else None,
    )

    subject_ids = [
        name for name in dat.dtype.names if name not in GLOBAL_DAT_SKIP_FIELDS
    ]
    log.info("Found %d subject field(s) under Dat (ignoring global Res)", len(subject_ids))

    parsed = 0
    for subject_id in sorted(subject_ids):
        try:
            subject_struct = dat[subject_id]
            subject = parse_subject(
                subject_struct,
                subject_id=subject_id,
                classification_lookup=classification_lookup,
                log=log,
            )
            database.add_subject(subject)
            parsed += 1
        except ParserError as exc:
            log.error("Subject %s: fatal parser error: %s", subject_id, exc)
            raise
        except ModelValidationError as exc:
            log.warning("Subject %s: skipped due to validation error: %s", subject_id, exc)
        except Exception as exc:  # noqa: BLE001 - keep other subjects
            log.warning("Subject %s: skipped due to unexpected error: %s", subject_id, exc)

    if parsed == 0:
        raise ParserError("No subjects could be parsed from Dat")

    # Lightweight parse summary
    session_total = sum(len(s.sessions) for s in database.iter_subjects())
    class_counts: Counter[str] = Counter()
    for subject in database.iter_subjects():
        for session in subject.sessions.values():
            class_counts[session.classification] += 1

    log.info(
        "Parsed MotionDatabase: %d subject(s), %d session(s), classes=%s",
        len(database),
        session_total,
        dict(class_counts),
    )
    return database


class MotionParser:
    """Object-oriented facade over the modular parse_* functions."""

    def __init__(
        self,
        *,
        catalog_path: str | Path | None = None,
        log: logging.Logger | None = None,
    ) -> None:
        self.catalog_path = catalog_path
        self.log = log or logger

    def parse(
        self,
        mat_data: dict[str, Any],
        *,
        dataset_path: str | Path | None = None,
    ) -> MotionDatabase:
        """Parse loaded MATLAB data into a :class:`MotionDatabase`."""
        return parse_database(
            mat_data,
            dataset_path=dataset_path,
            catalog_path=self.catalog_path,
            log=self.log,
        )
