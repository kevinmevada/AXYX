"""
Tests for motion_engine.loader.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from motion_engine.exceptions import LoaderError  # noqa: E402
from motion_engine.loader import DatasetLoader, load_motion_database  # noqa: E402

FILTERED_MAT = ROOT / "data" / "processed" / "Data_structure_filtered.mat"


class TestDatasetLoader(unittest.TestCase):
    def test_missing_dataset_raises(self) -> None:
        loader = DatasetLoader()
        with self.assertRaises(LoaderError):
            loader.load_raw(ROOT / "data" / "processed" / "does_not_exist.mat")

    @unittest.skipUnless(FILTERED_MAT.is_file(), "filtered MATLAB dataset not present")
    def test_load_raw_contains_dat(self) -> None:
        raw = DatasetLoader().load_raw(FILTERED_MAT)
        self.assertIn("Dat", raw)

    @unittest.skipUnless(FILTERED_MAT.is_file(), "filtered MATLAB dataset not present")
    def test_load_motion_database_convenience(self) -> None:
        db = load_motion_database(FILTERED_MAT)
        self.assertGreaterEqual(len(db.subjects), 1)


if __name__ == "__main__":
    unittest.main()
