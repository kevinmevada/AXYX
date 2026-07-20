"""
Validation tests for layout-aware frame count extraction.

Ensures marker trajectories stored as (N, 3) or (3, N) report the non-XYZ
dimension as frame count, and that unresolved layouts do not guess.
"""

import logging
import sys
import unittest
from pathlib import Path

import numpy as np

# Allow importing scripts/ without installing a package
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_motion_catalog import (  # noqa: E402
    detect_trajectory_layout,
    extract_frame_count_from_trajectory,
)


def _logger() -> logging.Logger:
    logger = logging.getLogger("test_frame_count")
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    logger.setLevel(logging.DEBUG)
    return logger


class TestDetectTrajectoryLayout(unittest.TestCase):
    def setUp(self) -> None:
        self.logger = _logger()

    def test_n_by_3_uses_axis0_as_frames(self) -> None:
        data = np.zeros((204, 3), dtype=float)
        layout = detect_trajectory_layout(data, self.logger, context="test")
        self.assertEqual(layout["layout"], "N,3")
        self.assertEqual(layout["frame_count"], 204)
        self.assertEqual(layout["coordinate_axis"], 1)
        self.assertEqual(layout["coordinate_dimensions"], 3)
        self.assertEqual(extract_frame_count_from_trajectory(data, self.logger), 204)

    def test_3_by_n_uses_axis1_as_frames(self) -> None:
        data = np.zeros((3, 306), dtype=float)
        layout = detect_trajectory_layout(data, self.logger, context="test")
        self.assertEqual(layout["layout"], "3,N")
        self.assertEqual(layout["frame_count"], 306)
        self.assertEqual(layout["coordinate_axis"], 0)
        self.assertEqual(extract_frame_count_from_trajectory(data, self.logger), 306)

    def test_never_reports_xyz_size_as_frames_for_n_by_3(self) -> None:
        """Regression: prior bug used shape[1] == 3 as frame count."""
        for n in (10, 100, 231, 340):
            data = np.random.randn(n, 3)
            frames = extract_frame_count_from_trajectory(data, self.logger)
            self.assertEqual(frames, n)
            self.assertNotEqual(frames, 3)

    def test_ambiguous_3_by_3_does_not_guess(self) -> None:
        data = np.zeros((3, 3), dtype=float)
        layout = detect_trajectory_layout(data, self.logger, context="ambiguous")
        self.assertIsNone(layout["layout"])
        self.assertIsNone(layout["frame_count"])
        self.assertIsNone(extract_frame_count_from_trajectory(data, self.logger))

    def test_neither_dim_equals_3_does_not_guess(self) -> None:
        data = np.zeros((10, 4), dtype=float)
        layout = detect_trajectory_layout(data, self.logger, context="no-xyz")
        self.assertIsNone(layout["layout"])
        self.assertIsNone(layout["frame_count"])
        self.assertIsNone(extract_frame_count_from_trajectory(data, self.logger))

    def test_non_2d_raises(self) -> None:
        with self.assertRaises(ValueError):
            detect_trajectory_layout(np.zeros(10), self.logger)
        with self.assertRaises(ValueError):
            detect_trajectory_layout(np.zeros((2, 3, 4)), self.logger)


class TestSessionClassificationContract(unittest.TestCase):
    """Lightweight checks that classification covers required categories."""

    def test_classify_session_categories(self) -> None:
        from build_motion_catalog import classify_session, session_classification_label

        cases = {
            "WU01": ("walking", "Walking"),
            "WU14": ("walking", "Walking"),  # beyond WU01-WU09
            "WU01Copy": ("walking_copy", "Walking Copy"),
            "static": ("calibration", "Calibration"),
            "staticCopy": ("calibration_copy", "Calibration Copy"),
            "WK01Copy": ("alternate_walking", "Alternate Walking"),
            "WU3": ("alternate_walking", "Alternate Walking"),
            "other_thing": ("unknown", "Unknown"),
        }
        for name, (key, label) in cases.items():
            self.assertEqual(classify_session(name), key, msg=name)
            self.assertEqual(session_classification_label(key), label, msg=name)


if __name__ == "__main__":
    unittest.main()
