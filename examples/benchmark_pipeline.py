#!/usr/bin/env python3
"""Benchmark-oriented pipeline example."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / "src"), str(REPO)]

from motion_engine.rendering.runtime import RuntimeFactory  # noqa: E402


def main() -> int:
    rt = RuntimeFactory().benchmark()
    report = rt.one_click(frames=200)
    print(report.as_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
