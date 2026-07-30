#!/usr/bin/env python3
"""Clinical demo — subject/trial/avatar → play gait."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / "src"), str(REPO)]

from motion_engine.rendering.runtime import RuntimeFactory  # noqa: E402


def main() -> int:
    rt = RuntimeFactory().debug()
    rt.startup()
    rt.select_subject("S2")
    rt.select_trial("WU01")
    rt.select_avatar("fixture")
    rt.select_mapping("test_two_bone")
    rt.prepare()
    rt.play()
    for i in range(20):
        fr = rt.tick()
        print(f"[{i}] t={fr.time:.3f}s bones={fr.bone_count} finite={fr.finite}")
    print("report", rt.report().as_dict())
    rt.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
