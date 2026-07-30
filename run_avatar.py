#!/usr/bin/env python3
"""Launch the skinned Army Girl avatar (NOT the clinical stick-figure Studio)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_PY = ROOT / "venv311" / "Scripts" / "python.exe"


def main() -> int:
    py = VENV_PY if VENV_PY.is_file() else Path(sys.executable)
    print("=" * 60)
    print("AXYX Digital Twin — Army Girl (skinned mesh)")
    print("NOT the stick-figure Studio (run_axyx.py).")
    print("=" * 60)
    env = os.environ.copy()
    env["QT_API"] = "pyside6"
    cmd = [
        str(py),
        "-m",
        "experiments.skinning_debug.run",
        "--army-girl",
        "--subject",
        "S2",
        "--session",
        "WU01",
    ]
    return subprocess.call(cmd, cwd=str(ROOT), env=env)


if __name__ == "__main__":
    raise SystemExit(main())
