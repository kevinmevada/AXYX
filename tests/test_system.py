"""
End-to-end integration suite for the Motion Engine foundation.

Certifies loader → parser → MotionDatabase against the production Motion Catalog
before Skeleton Builder / visualization work begins.

Run::

    pytest tests/test_system.py -v
"""

from __future__ import annotations

import json
import importlib
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from motion_engine.constants import (
    LAYOUT_3_BY_N,
    LAYOUT_N_BY_3,
    UNKNOWN_UNITS,
    VALID_TRAJECTORY_LAYOUTS,
)
from motion_engine.loader import DatasetLoader, load_motion_database
from motion_engine.models import MotionDatabase, ValidationReport
from motion_engine.parser import MotionParser, parse_database

ROOT = Path(__file__).resolve().parents[1]
FILTERED_MAT = ROOT / "data" / "processed" / "Data_structure_filtered.mat"
CATALOG_DIR = ROOT / "metadata" / "motion_catalog"
SCHEMA_PATH = CATALOG_DIR / "motion_schema.json"
SESSION_TYPES_PATH = CATALOG_DIR / "session_types.csv"

EXPECTED_SUBJECT_COUNT = 31
EXPECTED_MARKER_COUNT = 37
EXPECTED_JOINT_ANGLE_COUNT = 26
EXPECTED_JOINT_CENTER_COUNT = 6
EXPECTED_COM_COUNT = 2
EXPECTED_SEGMENT_COM_COUNT = 15
EXPECTED_CLINICAL_METRIC_COUNT = 10
EXPECTED_TOTAL_SESSIONS = 301

# Human-readable checklist used by the console certification report.
CERTIFICATION_CHECKS: list[tuple[str, str]] = [
    ("test_01_all_modules_import", "All modules import successfully"),
    ("test_02_dataset_loads_successfully", "Dataset loads successfully"),
    ("test_03_motion_database_created", "MotionDatabase is created"),
    ("test_04_subject_count_is_31", "Subject count is exactly 31"),
    ("test_05_all_expected_subject_ids_exist", "All expected subject IDs exist"),
    ("test_06_metadata_exists_for_every_subject", "Metadata exists for every subject"),
    ("test_07_sessions_parse_correctly", "Sessions parse correctly"),
    ("test_08_session_names_are_preserved", "Session names are preserved"),
    ("test_09_marker_count_is_37", "Marker count is exactly 37"),
    ("test_10_joint_angle_count_is_26", "Joint angle count is exactly 26"),
    ("test_11_joint_center_count_is_6", "Joint center count is exactly 6"),
    ("test_12_com_count_is_2", "Whole-body COM count is exactly 2"),
    ("test_13_segment_com_count_is_15", "Segment COM count is exactly 15"),
    ("test_14_clinical_metric_count_is_10", "Clinical metric count is exactly 10"),
    ("test_15_marker_trajectories_have_valid_frame_counts", "Marker trajectories contain valid frame counts"),
    ("test_16_trajectory_layouts_are_n3_or_3n", "Trajectory layouts are either N,3 or 3,N"),
    ("test_17_units_remain_unknown", "Units remain \"Unknown\""),
    ("test_18_motion_database_statistics_work", "MotionDatabase statistics work"),
    ("test_19_validator_works", "Validator works"),
    ("test_20_object_relationships_are_consistent", "Object relationships are internally consistent"),
    ("test_21_parsed_database_matches_motion_catalog", "Parsed database matches the Motion Catalog"),
]


def _load_catalog_schema() -> dict[str, Any]:
    assert SCHEMA_PATH.is_file(), f"Motion Catalog schema missing: {SCHEMA_PATH}"
    with SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _unique_variable_names(db: MotionDatabase, family: str) -> set[str]:
    names: set[str] = set()
    for subject in db.iter_subjects():
        for session in subject.sessions.values():
            kin = session.kinematics
            if family == "markers":
                names.update(kin.markers)
            elif family == "joint_angles":
                names.update(kin.joint_angles)
            elif family == "joint_centers":
                names.update(kin.joint_centers)
            elif family == "com":
                names.update(kin.com)
            elif family == "segment_com":
                names.update(kin.segment_com)
            elif family == "clinical_metrics":
                names.update(session.clinical_metrics)
            else:
                raise ValueError(f"Unknown family: {family}")
    return names


def _derive_database_statistics(db: MotionDatabase) -> dict[str, Any]:
    """Graph-level statistics from MotionDatabase (no MATLAB re-entry)."""
    frame_counts: list[int] = []
    class_counts: Counter[str] = Counter()
    session_names: set[str] = set()
    for subject in db.iter_subjects():
        for session in subject.sessions.values():
            session_names.add(session.name)
            class_counts[session.classification] += 1
            if session.frame_count is not None:
                frame_counts.append(session.frame_count)
    return {
        "subject_count": len(db.subjects),
        "session_count": sum(len(s.sessions) for s in db.iter_subjects()),
        "unique_session_names": len(session_names),
        "classification_histogram": dict(class_counts),
        "frame_count_min": min(frame_counts) if frame_counts else None,
        "frame_count_max": max(frame_counts) if frame_counts else None,
        "frame_count_mean": (
            sum(frame_counts) / len(frame_counts) if frame_counts else None
        ),
        "markers": sorted(_unique_variable_names(db, "markers")),
        "joint_angles": sorted(_unique_variable_names(db, "joint_angles")),
        "joint_centers": sorted(_unique_variable_names(db, "joint_centers")),
        "com": sorted(_unique_variable_names(db, "com")),
        "segment_com": sorted(_unique_variable_names(db, "segment_com")),
        "clinical_metrics": sorted(_unique_variable_names(db, "clinical_metrics")),
        "session_types": db.session_types(),
        "units_policy": db.units_policy(),
    }


@pytest.fixture(scope="module")
def catalog_schema() -> dict[str, Any]:
    return _load_catalog_schema()


@pytest.fixture(scope="module")
def expected_subject_ids(catalog_schema: dict[str, Any]) -> set[str]:
    return set(catalog_schema["subjects"]["ids"])


@pytest.fixture(scope="module")
def db() -> MotionDatabase:
    assert FILTERED_MAT.is_file(), (
        f"Filtered dataset missing at {FILTERED_MAT}. "
        "Cannot certify Motion Engine without Data_structure_filtered.mat."
    )
    database = load_motion_database(FILTERED_MAT, catalog_path=CATALOG_DIR)
    assert isinstance(database, MotionDatabase)
    return database


# ---------------------------------------------------------------------------
# Certification checks
# ---------------------------------------------------------------------------


class TestMotionEngineSystem:
    """Ordered end-to-end certification checks (01-21)."""

    def test_01_all_modules_import(self) -> None:
        modules = [
            "motion_engine",
            "motion_engine.models",
            "motion_engine.parser",
            "motion_engine.loader",
            "motion_engine.validator",
            "motion_engine.statistics",
            "motion_engine.constants",
            "motion_engine.typing",
            "motion_engine.exceptions",
            "motion_engine.utils",
        ]
        failures: list[str] = []
        for name in modules:
            try:
                importlib.import_module(name)
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{name}: {exc}")
        assert not failures, "Module import failures:\n" + "\n".join(failures)

    def test_02_dataset_loads_successfully(self) -> None:
        loader = DatasetLoader(catalog_path=CATALOG_DIR)
        raw = loader.load_raw(FILTERED_MAT)
        assert "Dat" in raw, "Loaded MATLAB dict is missing top-level 'Dat'"
        assert raw["Dat"].dtype.names, "Dat has no struct fields"

    def test_03_motion_database_created(self, db: MotionDatabase) -> None:
        assert isinstance(db, MotionDatabase), (
            f"Expected MotionDatabase, got {type(db)!r}"
        )
        via_api = MotionDatabase().load(FILTERED_MAT)
        assert isinstance(via_api, MotionDatabase)
        assert len(via_api.subjects) == len(db.subjects)

    def test_04_subject_count_is_31(self, db: MotionDatabase) -> None:
        actual = len(db.subjects)
        assert actual == EXPECTED_SUBJECT_COUNT, (
            f"Expected exactly {EXPECTED_SUBJECT_COUNT} subjects, found {actual}. "
            f"IDs={db.list_subjects()}"
        )

    def test_05_all_expected_subject_ids_exist(
        self,
        db: MotionDatabase,
        expected_subject_ids: set[str],
    ) -> None:
        actual = set(db.list_subjects())
        missing = sorted(expected_subject_ids - actual)
        unexpected = sorted(actual - expected_subject_ids)
        assert not missing and not unexpected, (
            f"Subject ID mismatch.\n"
            f"Missing ({len(missing)}): {missing}\n"
            f"Unexpected ({len(unexpected)}): {unexpected}"
        )

    def test_06_metadata_exists_for_every_subject(self, db: MotionDatabase) -> None:
        incomplete: list[str] = []
        for subject in db.iter_subjects():
            meta = subject.metadata
            if meta is None:
                incomplete.append(f"{subject.id}: metadata is None")
                continue
            # Soft but required clinical anthropometrics / rates from catalog.
            required = {
                "vrate": meta.vrate,
                "fprate": meta.fprate,
                "mass": meta.mass,
                "height": meta.height,
                "lleg_length": meta.lleg_length,
                "rleg_length": meta.rleg_length,
            }
            missing_fields = [k for k, v in required.items() if v is None]
            if missing_fields:
                incomplete.append(f"{subject.id}: missing {missing_fields}")
        assert not incomplete, (
            "Metadata incomplete for subject(s):\n" + "\n".join(incomplete)
        )

    def test_07_sessions_parse_correctly(self, db: MotionDatabase) -> None:
        empty_subjects = [
            subject.id for subject in db.iter_subjects() if not subject.sessions
        ]
        total_sessions = sum(len(s.sessions) for s in db.iter_subjects())
        assert not empty_subjects, (
            f"Subjects with zero sessions: {empty_subjects}"
        )
        assert total_sessions == EXPECTED_TOTAL_SESSIONS, (
            f"Expected {EXPECTED_TOTAL_SESSIONS} total sessions from catalog, "
            f"found {total_sessions}"
        )
        # Spot-check a known canonical walking session.
        s2 = db.get_subject("S2")
        assert s2.has_session("WU01"), "S2 missing expected session WU01"
        wu01 = s2.get_session("WU01")
        assert wu01.kinematics.markers, "S2/WU01 parsed with empty markers"

    def test_08_session_names_are_preserved(
        self,
        db: MotionDatabase,
        catalog_schema: dict[str, Any],
    ) -> None:
        catalog_names = set(catalog_schema["sessions"]["unique_names"])
        parsed_names = {
            session.name
            for subject in db.iter_subjects()
            for session in subject.sessions.values()
        }
        # Keys in subject.sessions must equal Session.name (no renaming).
        mismatched_keys = [
            f"{subject.id}:{key}!={session.name}"
            for subject in db.iter_subjects()
            for key, session in subject.sessions.items()
            if key != session.name
        ]
        assert not mismatched_keys, (
            "Session dict keys diverge from original names:\n"
            + "\n".join(mismatched_keys[:20])
        )
        missing = sorted(catalog_names - parsed_names)
        unexpected = sorted(parsed_names - catalog_names)
        assert not missing and not unexpected, (
            f"Session name set mismatch vs Motion Catalog.\n"
            f"Missing: {missing}\nUnexpected: {unexpected}"
        )
        # Alternate naming for S12 must remain Copy/WK originals.
        s12_names = db.get_subject("S12").list_sessions()
        assert any(name.endswith("Copy") for name in s12_names), (
            f"S12 original Copy session names were not preserved: {s12_names}"
        )

    def test_09_marker_count_is_37(self, db: MotionDatabase) -> None:
        names = _unique_variable_names(db, "markers")
        assert len(names) == EXPECTED_MARKER_COUNT, (
            f"Expected {EXPECTED_MARKER_COUNT} unique markers, found {len(names)}: "
            f"{sorted(names)}"
        )

    def test_10_joint_angle_count_is_26(self, db: MotionDatabase) -> None:
        names = _unique_variable_names(db, "joint_angles")
        assert len(names) == EXPECTED_JOINT_ANGLE_COUNT, (
            f"Expected {EXPECTED_JOINT_ANGLE_COUNT} unique joint angles, "
            f"found {len(names)}: {sorted(names)}"
        )

    def test_11_joint_center_count_is_6(self, db: MotionDatabase) -> None:
        names = _unique_variable_names(db, "joint_centers")
        assert len(names) == EXPECTED_JOINT_CENTER_COUNT, (
            f"Expected {EXPECTED_JOINT_CENTER_COUNT} unique joint centers, "
            f"found {len(names)}: {sorted(names)}"
        )

    def test_12_com_count_is_2(self, db: MotionDatabase) -> None:
        names = _unique_variable_names(db, "com")
        assert len(names) == EXPECTED_COM_COUNT, (
            f"Expected {EXPECTED_COM_COUNT} unique whole-body COM variables, "
            f"found {len(names)}: {sorted(names)}"
        )

    def test_13_segment_com_count_is_15(self, db: MotionDatabase) -> None:
        names = _unique_variable_names(db, "segment_com")
        assert len(names) == EXPECTED_SEGMENT_COM_COUNT, (
            f"Expected {EXPECTED_SEGMENT_COM_COUNT} unique segment COM variables, "
            f"found {len(names)}: {sorted(names)}"
        )

    def test_14_clinical_metric_count_is_10(self, db: MotionDatabase) -> None:
        names = _unique_variable_names(db, "clinical_metrics")
        assert len(names) == EXPECTED_CLINICAL_METRIC_COUNT, (
            f"Expected {EXPECTED_CLINICAL_METRIC_COUNT} unique clinical metrics, "
            f"found {len(names)}: {sorted(names)}"
        )

    def test_15_marker_trajectories_have_valid_frame_counts(
        self,
        db: MotionDatabase,
    ) -> None:
        """Frame counts must be resolved and not stuck at the XYZ axis size (3)."""
        invalid: list[str] = []
        stuck_at_three = 0
        resolved = 0
        for subject in db.iter_subjects():
            for session in subject.sessions.values():
                for name, marker in session.kinematics.markers.items():
                    frames = marker.trajectory.n_frames
                    path = f"{subject.id}/{session.name}/{name}"
                    if frames is None:
                        invalid.append(f"{path}: n_frames is None")
                        continue
                    if frames <= 0:
                        invalid.append(f"{path}: non-positive n_frames={frames}")
                        continue
                    resolved += 1
                    if frames == 3:
                        stuck_at_three += 1
        assert not invalid, (
            "Invalid marker frame counts:\n" + "\n".join(invalid[:30])
        )
        assert resolved > 0, "No resolved marker trajectories found"
        # Prior axis-swap bug signature: every trajectory reports 3 frames.
        assert stuck_at_three < resolved, (
            f"Frame-count regression suspected: {stuck_at_three}/{resolved} "
            "marker trajectories report exactly 3 frames (XYZ axis size)."
        )
        # Session-level frame counts must also clear the same guardrail.
        session_frames = [
            session.frame_count
            for subject in db.iter_subjects()
            for session in subject.sessions.values()
            if session.frame_count is not None
        ]
        assert session_frames, "No session frame_count values were resolved"
        assert min(session_frames) > 3, (
            f"Session frame_count min={min(session_frames)} looks like XYZ-axis swap bug"
        )

    def test_16_trajectory_layouts_are_n3_or_3n(self, db: MotionDatabase) -> None:
        bad: list[str] = []
        for subject in db.iter_subjects():
            for session in subject.sessions.values():
                for family_name, collection in (
                    ("marker", session.kinematics.markers),
                    ("joint_angle", session.kinematics.joint_angles),
                    ("joint_center", session.kinematics.joint_centers),
                    ("com", session.kinematics.com),
                    ("segment_com", session.kinematics.segment_com),
                ):
                    for name, variable in collection.items():
                        layout = variable.trajectory.layout
                        if layout not in VALID_TRAJECTORY_LAYOUTS:
                            bad.append(
                                f"{subject.id}/{session.name}/{family_name}/{name}: "
                                f"layout={layout!r}"
                            )
                if (
                    session.trajectory_layout is not None
                    and session.trajectory_layout not in VALID_TRAJECTORY_LAYOUTS
                ):
                    bad.append(
                        f"{subject.id}/{session.name}: "
                        f"session.trajectory_layout={session.trajectory_layout!r}"
                    )
        assert not bad, (
            "Unsupported trajectory layouts "
            f"(allowed: {LAYOUT_N_BY_3!r}, {LAYOUT_3_BY_N!r}):\n"
            + "\n".join(bad[:40])
        )

    def test_17_units_remain_unknown(self, db: MotionDatabase) -> None:
        bad: list[str] = []
        for subject in db.iter_subjects():
            for session in subject.sessions.values():
                for family, collection in (
                    ("marker", session.kinematics.markers),
                    ("joint_angle", session.kinematics.joint_angles),
                    ("joint_center", session.kinematics.joint_centers),
                    ("com", session.kinematics.com),
                    ("segment_com", session.kinematics.segment_com),
                ):
                    for name, variable in collection.items():
                        if variable.units != UNKNOWN_UNITS:
                            bad.append(
                                f"{subject.id}/{session.name}/{family}/{name}: "
                                f"units={variable.units!r}"
                            )
                for name, metric in session.clinical_metrics.items():
                    if metric.units != UNKNOWN_UNITS:
                        bad.append(
                            f"{subject.id}/{session.name}/metric/{name}: "
                            f"units={metric.units!r}"
                        )
        policy = db.units_policy()
        assert policy["default_units"] == UNKNOWN_UNITS
        assert not bad, (
            f"Units must remain {UNKNOWN_UNITS!r}; found overrides:\n"
            + "\n".join(bad[:40])
        )

    def test_18_motion_database_statistics_work(self, db: MotionDatabase) -> None:
        """Statistics are obtainable from MotionDatabase without MATLAB re-entry.

        Uses public graph APIs (``session_types``, ``units_policy``) plus a
        derived aggregate report. ``StatisticsEngine`` remains a future module.
        """
        session_types = db.session_types()
        assert isinstance(session_types, list) and session_types, (
            "MotionDatabase.session_types() returned no rows"
        )
        for row in session_types:
            assert "original_name" in row and "classification" in row
            assert row["frequency"] >= 1

        units_policy = db.units_policy()
        assert units_policy["default_units"] == UNKNOWN_UNITS

        stats = _derive_database_statistics(db)
        assert stats["subject_count"] == EXPECTED_SUBJECT_COUNT
        assert stats["session_count"] == EXPECTED_TOTAL_SESSIONS
        assert stats["frame_count_min"] is not None
        assert stats["frame_count_max"] is not None
        assert stats["frame_count_min"] > 3
        assert len(stats["markers"]) == EXPECTED_MARKER_COUNT
        assert len(stats["clinical_metrics"]) == EXPECTED_CLINICAL_METRIC_COUNT

        # Engine module must at least import for the package surface.
        from motion_engine.statistics import StatisticsEngine

        engine = StatisticsEngine()
        assert callable(engine.summarize)

    def test_19_validator_works(self, db: MotionDatabase) -> None:
        """Structural validator on MotionDatabase must pass for the filtered set."""
        report = db.validate()
        assert isinstance(report, ValidationReport), (
            f"Expected ValidationReport, got {type(report)!r}"
        )
        assert report.ok, (
            "MotionDatabase.validate() failed with errors:\n"
            + "\n".join(report.errors[:40])
        )

        from motion_engine.validator import DatabaseValidator

        validator = DatabaseValidator()
        assert callable(validator.validate)

    def test_20_object_relationships_are_consistent(self, db: MotionDatabase) -> None:
        problems: list[str] = []
        for subject_id, subject in db.subjects.items():
            if subject_id != subject.id:
                problems.append(
                    f"DB key {subject_id!r} != subject.id {subject.id!r}"
                )
            for session_name, session in subject.sessions.items():
                if session_name != session.name:
                    problems.append(
                        f"{subject.id}: key {session_name!r} != "
                        f"session.name {session.name!r}"
                    )
                if session.subject_id != subject.id:
                    problems.append(
                        f"{subject.id}/{session.name}: session.subject_id="
                        f"{session.subject_id!r}"
                    )
                kin = session.kinematics
                for name, marker in kin.markers.items():
                    if name != marker.name:
                        problems.append(
                            f"{subject.id}/{session.name}: marker key {name!r} "
                            f"!= {marker.name!r}"
                        )
                    if marker.trajectory is None:
                        problems.append(
                            f"{subject.id}/{session.name}/{name}: trajectory is None"
                        )
                for name, metric in session.clinical_metrics.items():
                    if name != metric.name:
                        problems.append(
                            f"{subject.id}/{session.name}: metric key {name!r} "
                            f"!= {metric.name!r}"
                        )
                # Ownership: Session owns kinematics + clinical metrics.
                assert session.kinematics is kin
        assert not problems, (
            "Relationship consistency failures:\n" + "\n".join(problems[:40])
        )

    def test_21_parsed_database_matches_motion_catalog(
        self,
        db: MotionDatabase,
        catalog_schema: dict[str, Any],
    ) -> None:
        stats = _derive_database_statistics(db)
        dataset = catalog_schema["dataset"]
        assert stats["subject_count"] == dataset["total_subjects"]
        assert stats["session_count"] == dataset["total_sessions"]
        assert stats["unique_session_names"] == dataset["unique_session_types"]

        kin = catalog_schema["kinematics"]
        assert stats["markers"] == sorted(kin["markers"])
        assert stats["joint_angles"] == sorted(kin["joint_angles"])
        assert stats["joint_centers"] == sorted(kin["joint_centers"])
        assert stats["com"] == sorted(kin["center_of_mass"])
        assert stats["segment_com"] == sorted(kin["segment_com"])
        assert stats["clinical_metrics"] == sorted(
            catalog_schema["clinical_metrics"]["available"]
        )

        # Session type classifications should align with catalog CSV when present.
        if SESSION_TYPES_PATH.is_file():
            import csv

            catalog_class: dict[str, str] = {}
            with SESSION_TYPES_PATH.open("r", encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    catalog_class[row["Original Name"]] = row["Classification"]
            mismatches = []
            for row in stats["session_types"]:
                expected = catalog_class.get(row["original_name"])
                if expected is not None and row["classification"] != expected:
                    mismatches.append(
                        f"{row['original_name']}: parsed={row['classification']!r} "
                        f"catalog={expected!r}"
                    )
            assert not mismatches, (
                "Session classification diverges from session_types.csv:\n"
                + "\n".join(mismatches[:20])
            )


def test_parser_facade_matches_loader(db: MotionDatabase) -> None:
    """Secondary sanity: MotionParser facade yields the same subject inventory."""
    raw = DatasetLoader().load_raw(FILTERED_MAT)
    via_parser = MotionParser(catalog_path=CATALOG_DIR).parse(
        raw, dataset_path=FILTERED_MAT
    )
    assert set(via_parser.list_subjects()) == set(db.list_subjects())
    # parse_database entry point must agree as well.
    via_fn = parse_database(
        raw, dataset_path=FILTERED_MAT, catalog_path=CATALOG_DIR
    )
    assert len(via_fn.subjects) == len(db.subjects)
