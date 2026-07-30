#!/usr/bin/env python3
"""Performance demo — cold vs warm start."""

from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / "src"), str(REPO)]

from motion_engine.rendering.runtime import RuntimeFactory  # noqa: E402


def main() -> int:
    # cold
    t0 = time.perf_counter()
    rt = RuntimeFactory().benchmark()
    cold = rt.one_click(frames=100)
    cold_s = time.perf_counter() - t0
    # warm (second runtime, avatar cache cold per-instance but imports warm)
    t1 = time.perf_counter()
    rt2 = RuntimeFactory().benchmark()
    warm = rt2.one_click(frames=100)
    warm_s = time.perf_counter() - t1
    print("cold_s", round(cold_s, 3), "fps", round(cold.fps, 1))
    print("warm_s", round(warm_s, 3), "fps", round(warm.fps, 1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
