"""Entry point helpers for AXYX."""

from __future__ import annotations

import logging
import os
import sys
from typing import Sequence

# Prefer PySide6 for pyvistaqt / Qt binding before any Qt imports.
os.environ.setdefault("QT_API", "pyside6")
# Clinical tools run on varied Windows DPI setups - enable Qt HiDPI early.
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

from motion_engine.studio.application import StudioApplication


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging for the studio process."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def run_studio(
    argv: Sequence[str] | None = None,
    *,
    auto_open: bool = False,
) -> int:
    """Launch AXYX.

    Args:
        argv: Optional Qt argv list.
        auto_open: Open the default dataset immediately after splash.

    Returns:
        Qt application exit code.
    """
    configure_logging()
    args = list(argv) if argv is not None else sys.argv
    app = StudioApplication(argv=args)
    return app.run(auto_open=auto_open)


def main() -> None:
    """Console-script style entry point."""
    raise SystemExit(run_studio())


if __name__ == "__main__":
    main()
