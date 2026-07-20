"""Launch AXYX research studio."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_API", "pyside6")

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from motion_engine.studio.app import run_studio


if __name__ == "__main__":
    raise SystemExit(run_studio(auto_open=False))
