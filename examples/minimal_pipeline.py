#!/usr/bin/env python3
"""Minimal Digital Twin Runtime pipeline example."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / "src"), str(REPO)]

from motion_engine.rendering.runtime import RuntimeFactory  # noqa: E402


def main() -> int:
    rt = RuntimeFactory().debug()
    report = rt.one_click(avatar="fixture", frames=30)
    print("frames", report.frames)
    print("fps", round(report.fps, 1))
    print("frame_ms", round(report.frame_time_ms, 3))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
