"""
Meaningful unit tests for motion_engine.models.

These tests construct domain objects in memory without MATLAB I/O.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from motion_engine.constants import (  # noqa: E402
    SESSION_CLASS_WALKING,
    UNKNOWN_UNITS,
)
from motion_engine.exceptions import (  # noqa: E402
    ModelValidationError,
    SessionNotFoundError,
    SubjectNotFoundError,
    VariableNotFoundError,
)
from motion_engine.models import (  # noqa: E402
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


def _n_by_3(n_frames: int = 10) -> Trajectory:
    return Trajectory(
        coordinates=np.zeros((n_frames, 3), dtype=float),
        n_frames=n_frames,
        layout="N,3",
        coordinate_axis=1,
        units=UNKNOWN_UNITS,
    )


class TestTrajectory(unittest.TestCase):
    def test_n_by_3_valid(self) -> None:
        traj = _n_by_3(204)
        self.assertEqual(traj.n_frames, 204)
        self.assertEqual(traj.layout, "N,3")
        self.assertEqual(traj.shape, (204, 3))
        self.assertTrue(traj.is_resolved)
        self.assertIn("Trajectory", repr(traj))

    def test_3_by_n_valid(self) -> None:
        traj = Trajectory(
            coordinates=np.zeros((3, 100), dtype=float),
            n_frames=100,
            layout="3,N",
            coordinate_axis=0,
        )
        self.assertEqual(traj.n_frames, 100)
        self.assertTrue(traj.is_resolved)

    def test_rejects_non_2d(self) -> None:
        with self.assertRaises(ModelValidationError):
            Trajectory(coordinates=np.zeros(10), n_frames=10, layout="N,3")

    def test_rejects_layout_shape_mismatch(self) -> None:
        with self.assertRaises(ModelValidationError):
            Trajectory(
                coordinates=np.zeros((10, 3), dtype=float),
                n_frames=10,
                layout="3,N",
            )

    def test_rejects_n_frames_mismatch(self) -> None:
        with self.assertRaises(ModelValidationError):
            Trajectory(
                coordinates=np.zeros((10, 3), dtype=float),
                n_frames=11,
                layout="N,3",
            )


class TestMarkerFamilies(unittest.TestCase):
    def test_marker_reuses_trajectory(self) -> None:
        traj = _n_by_3(12)
        marker = Marker(name="LFHD", trajectory=traj)
        self.assertEqual(marker.n_frames, 12)
        self.assertEqual(marker.units, UNKNOWN_UNITS)
        self.assertIs(marker.trajectory, traj)

    def test_joint_angle_series_property(self) -> None:
        traj = _n_by_3(8)
        angle = JointAngle(name="LKneeAngles", trajectory=traj)
        self.assertEqual(angle.series.shape, (8, 3))
        self.assertIsNone(angle.rotation_axes)

    def test_joint_center_com_segment(self) -> None:
        traj = _n_by_3(5)
        self.assertEqual(JointCenter(name="LHJC", trajectory=traj).name, "LHJC")
        self.assertEqual(
            CenterOfMass(name="CentreOfMass", trajectory=traj).n_frames, 5
        )
        self.assertEqual(SegmentCOM(name="PelvisCOM", trajectory=traj).units, UNKNOWN_UNITS)

    def test_empty_name_rejected(self) -> None:
        with self.assertRaises(ModelValidationError):
            Marker(name="", trajectory=_n_by_3())


class TestClinicalMetric(unittest.TestCase):
    def test_is_not_trajectory(self) -> None:
        metric = ClinicalMetric(name="StpLen", value=1.23)
        self.assertEqual(metric.units, UNKNOWN_UNITS)
        self.assertIsNone(metric.description)
        self.assertFalse(hasattr(metric, "trajectory"))


class TestKinematicsSessionSubject(unittest.TestCase):
    def test_kinematics_lookup(self) -> None:
        kin = Kinematics(
            markers={"LFHD": Marker(name="LFHD", trajectory=_n_by_3(4))}
        )
        self.assertEqual(kin.list_markers(), ["LFHD"])
        self.assertEqual(kin.get_marker("LFHD").name, "LFHD")
        with self.assertRaises(VariableNotFoundError):
            kin.get_marker("NOPE")

    def test_session_owns_kinematics_and_metrics(self) -> None:
        session = Session(
            name="WU01",
            subject_id="S2",
            classification=SESSION_CLASS_WALKING,
            frame_count=4,
            trajectory_layout="N,3",
            sampling_rate_hz=100.0,
            kinematics=Kinematics(
                markers={"LFHD": Marker(name="LFHD", trajectory=_n_by_3(4))}
            ),
            clinical_metrics={
                "WkVel": ClinicalMetric(name="WkVel", value=1.1),
            },
        )
        self.assertEqual(session.get_metric("WkVel").value, 1.1)
        self.assertIn("Session", repr(session))

    def test_session_rejects_bad_classification(self) -> None:
        with self.assertRaises(ModelValidationError):
            Session(
                name="WU01",
                subject_id="S2",
                classification="NotARealClass",
            )

    def test_subject_session_access(self) -> None:
        session = Session(
            name="WU01",
            subject_id="S2",
            classification=SESSION_CLASS_WALKING,
            frame_count=4,
        )
        subject = Subject(
            id="S2",
            metadata=Metadata(vrate=100.0, fprate=1000.0, mass=70.0),
            sessions={"WU01": session},
        )
        self.assertEqual(subject.list_sessions(), ["WU01"])
        self.assertTrue(subject.has_session("WU01"))
        self.assertEqual(subject.get_session("WU01").name, "WU01")
        self.assertEqual(len(subject.sessions_by_class(SESSION_CLASS_WALKING)), 1)
        with self.assertRaises(SessionNotFoundError):
            subject.get_session("missing")
        summary = subject.summary()
        self.assertEqual(summary["subject_id"], "S2")
        self.assertEqual(summary["session_count"], 1)

    def test_subject_add_session_id_mismatch(self) -> None:
        subject = Subject(id="S2")
        bad = Session(name="WU01", subject_id="S9")
        with self.assertRaises(ModelValidationError):
            subject.add_session(bad)


class TestMotionDatabase(unittest.TestCase):
    def _sample_db(self) -> MotionDatabase:
        db = MotionDatabase(dataset_path=Path("data/processed/Data_structure_filtered.mat"))
        subject = Subject(
            id="S2",
            metadata=Metadata(vrate=100.0),
            sessions={
                "WU01": Session(
                    name="WU01",
                    subject_id="S2",
                    classification=SESSION_CLASS_WALKING,
                    frame_count=10,
                ),
                "static": Session(
                    name="static",
                    subject_id="S2",
                    classification="Calibration",
                    frame_count=50,
                ),
            },
        )
        db.add_subject(subject)
        return db

    def test_lookup_helpers(self) -> None:
        db = self._sample_db()
        self.assertEqual(len(db), 1)
        self.assertIn("S2", db)
        self.assertTrue(db.has_subject("S2"))
        self.assertEqual(db.list_subjects(), ["S2"])
        self.assertEqual(db.get_subject("S2").id, "S2")
        self.assertEqual(list(db.iter_subjects())[0].id, "S2")
        with self.assertRaises(SubjectNotFoundError):
            db.get_subject("S999")

    def test_statistics_not_implemented(self) -> None:
        db = MotionDatabase()
        with self.assertRaises(NotImplementedError):
            db.statistics()

    def test_validate_and_session_types(self) -> None:
        db = self._sample_db()
        report = db.validate()
        self.assertTrue(report.ok)
        types = db.session_types()
        names = {row["original_name"] for row in types}
        self.assertEqual(names, {"WU01", "static"})
        policy = db.units_policy()
        self.assertEqual(policy["default_units"], UNKNOWN_UNITS)

    def test_empty_database_warns(self) -> None:
        report = MotionDatabase().validate()
        self.assertTrue(report.ok)
        self.assertTrue(any("no subjects" in warning for warning in report.warnings))

    def test_metadata_rejects_inverted_frames(self) -> None:
        with self.assertRaises(ModelValidationError):
            Subject(
                id="S2",
                metadata=Metadata(first_frame=10, last_frame=1),
            )


if __name__ == "__main__":
    unittest.main()
