"""
Tests for motion_engine.parser against the filtered clinical gait dataset.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from motion_engine.constants import UNKNOWN_UNITS  # noqa: E402
from motion_engine.exceptions import ParserError  # noqa: E402
from motion_engine.loader import load_motion_database  # noqa: E402
from motion_engine.models import MotionDatabase  # noqa: E402
from motion_engine.parser import parse_database  # noqa: E402
from motion_engine.utils import (  # noqa: E402
    categorize_kinematic_variable,
    classify_session_name,
    detect_trajectory_layout,
)

FILTERED_MAT = ROOT / "data" / "processed" / "Data_structure_filtered.mat"


@unittest.skipUnless(FILTERED_MAT.is_file(), "filtered MATLAB dataset not present")
class TestParseFilteredDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db = load_motion_database(FILTERED_MAT)

    def test_subject_count(self) -> None:
        self.assertEqual(len(self.db.subjects), 31)
        self.assertEqual(len(self.db), 31)

    def test_get_subject_s2(self) -> None:
        subject = self.db.get_subject("S2")
        self.assertEqual(subject.id, "S2")
        self.assertTrue(subject.sessions)
        self.assertIsNotNone(subject.metadata.vrate)

    def test_marker_trajectory_access(self) -> None:
        subject = self.db.get_subject("S2")
        session = subject.get_session("WU01")
        marker = session.kinematics.markers["LFHD"]
        self.assertEqual(marker.name, "LFHD")
        self.assertEqual(marker.units, UNKNOWN_UNITS)
        self.assertIsNotNone(marker.trajectory)
        self.assertTrue(marker.trajectory.is_resolved)
        self.assertGreater(marker.trajectory.n_frames or 0, 3)
        self.assertEqual(marker.trajectory.layout, "N,3")

    def test_motion_database_load_api(self) -> None:
        db = MotionDatabase().load(FILTERED_MAT)
        self.assertEqual(len(db.subjects), 31)
        self.assertIn("LFHD", db.get_subject("S2").get_session("WU01").kinematics.markers)

    def test_clinical_metrics_from_res(self) -> None:
        session = self.db.get_subject("S2").get_session("WU01")
        self.assertTrue(session.clinical_metrics)
        self.assertIn("WkVel", session.clinical_metrics)
        self.assertEqual(session.clinical_metrics["WkVel"].units, UNKNOWN_UNITS)

    def test_session_names_preserved(self) -> None:
        # S12 uses alternate WK*Copy naming - must remain original names.
        subject = self.db.get_subject("S12")
        self.assertTrue(any(name.endswith("Copy") for name in subject.list_sessions()))


class TestParserHelpers(unittest.TestCase):
    def test_layout_detection(self) -> None:
        import numpy as np

        layout = detect_trajectory_layout(np.zeros((204, 3)))
        self.assertEqual(layout["layout"], "N,3")
        self.assertEqual(layout["frame_count"], 204)

    def test_categorize_and_classify(self) -> None:
        self.assertEqual(categorize_kinematic_variable("LFHD"), "markers")
        self.assertEqual(categorize_kinematic_variable("LKneeAngles"), "joint_angles")
        self.assertEqual(categorize_kinematic_variable("LHJC"), "joint_centers")
        self.assertEqual(categorize_kinematic_variable("CentreOfMass"), "center_of_mass")
        self.assertEqual(categorize_kinematic_variable("PelvisCOM"), "segment_com")
        self.assertEqual(classify_session_name("WU01"), "Walking")
        self.assertEqual(classify_session_name("static"), "Calibration")
        self.assertEqual(classify_session_name("WK01Copy"), "Alternate Walking")

    def test_parse_database_requires_dat(self) -> None:
        with self.assertRaises(ParserError):
            parse_database({})


if __name__ == "__main__":
    unittest.main()
