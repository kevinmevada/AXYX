"""Launch AXYX research studio (alias for run_axyx.py)."""

from __future__ import annotations

import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).with_name("run_axyx.py")), run_name="__main__")
