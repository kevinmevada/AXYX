#!/usr/bin/env python3
"""Retarget showcase — clinical gait onto avatar with mirror option."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / "src"), str(REPO)]

from motion_engine.rendering.runtime import DigitalTwinRuntime  # noqa: E402
from motion_engine.rendering.runtime.runtime_configuration import get_preset  # noqa: E402


def main() -> int:
    cfg = get_preset("debug")
    cfg.mirror = True
    cfg.root_motion = "world"
    cfg.synthetic_frames = 40
    rt = DigitalTwinRuntime(cfg)
    rt.startup()
    rt.select_avatar("fixture")
    rt.select_mapping("test_two_bone")
    for fr in rt.run_frames(20):
        if fr.index % 5 == 0:
            print(fr.index, fr.stages_ns.get("retarget"), "ns retarget")
    print(rt.profiler_summary().get("retarget"))
    rt.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
