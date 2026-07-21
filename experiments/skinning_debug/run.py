"""Entry point: ``python -m experiments.skinning_debug.run``."""

from __future__ import annotations

import os
import sys

# Must be set before any PySide6 / pyvistaqt import (PyQt5 is also installed).
os.environ["QT_API"] = "pyside6"


def _require_viewer_deps() -> None:
    missing: list[str] = []
    try:
        import pyvista  # noqa: F401
    except ImportError:
        missing.append("pyvista")
    try:
        import pyvistaqt  # noqa: F401
    except ImportError:
        missing.append("pyvistaqt")
    try:
        import PySide6  # noqa: F401
    except ImportError:
        missing.append("PySide6")
    if not missing:
        return
    exe = sys.executable
    pkgs = " ".join(missing)
    print(
        "Missing viewer dependencies: "
        + ", ".join(missing)
        + f"\n\nUse the project venv, then install:\n"
        f"  {exe} -m pip install {pkgs}\n\n"
        "Windows:\n"
        "  .\\venv311\\Scripts\\Activate.ps1\n"
        "  python -m experiments.skinning_debug.run --fixture\n",
        file=sys.stderr,
    )
    raise SystemExit(1)


_require_viewer_deps()

from experiments.skinning_debug.app import main

if __name__ == "__main__":
    raise SystemExit(main())
