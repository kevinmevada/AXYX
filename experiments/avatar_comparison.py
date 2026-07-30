#!/usr/bin/env python3
"""Compare fixture / army_girl / metahuman via runtime (asset fallbacks allowed)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / "src"), str(REPO)]

from motion_engine.rendering.runtime import RuntimeFactory  # noqa: E402


def main() -> int:
    rt = RuntimeFactory().debug()
    rt.startup()
    for avatar in ("fixture", "army_girl", "metahuman"):
        rt.select_avatar(avatar)
        rt.select_mapping("test_two_bone" if avatar == "fixture" else "matlab_clinical_to_army_girl")
        rt.prepare()
        fr = rt.seek(0)
        print(f"{avatar:12s} resolved={rt.session.avatar_name:20s} bones={fr.bone_count} verts={fr.vertex_count}")
    rt.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
