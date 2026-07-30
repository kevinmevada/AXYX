#!/usr/bin/env python3
"""Clinical-style pipeline: subject/trial selection + retarget gait."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / "src"), str(REPO)]

from motion_engine.rendering.runtime import RuntimeFactory  # noqa: E402


def main() -> int:
    rt = RuntimeFactory().from_preset("research")
    # Force fixture-safe mapping for CI / machines without Army Girl FBX
    rt.config.avatar = "fixture"
    rt.config.mapping_profile = "test_two_bone"
    rt.config.synthetic_frames = 60
    rt.startup()
    rt.select_subject("S2")
    rt.select_trial("WU01")
    rt.select_avatar("fixture")
    rt.select_mapping("test_two_bone")
    rt.prepare()
    rt.play()
    for _ in range(30):
        fr = rt.tick()
        print(f"frame={fr.index} verts={fr.vertex_count} finite={fr.finite}")
    print(rt.report().as_dict())
    rt.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
