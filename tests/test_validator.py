"""
Placeholder tests for motion_engine.validator.

TODO: Implement once DatabaseValidator performs catalog-aware checks.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from motion_engine.validator import DatabaseValidator  # noqa: E402


class TestDatabaseValidatorPlaceholder(unittest.TestCase):
    def test_validate_not_implemented(self) -> None:
        validator = DatabaseValidator()
        with self.assertRaises(NotImplementedError):
            validator.validate(object())


if __name__ == "__main__":
    unittest.main()
