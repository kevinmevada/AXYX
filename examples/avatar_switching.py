#!/usr/bin/env python3
"""Switch avatars within one runtime session."""

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
        if avatar == "fixture":
            rt.select_mapping("test_two_bone")
        else:
            rt.select_mapping("matlab_clinical_to_army_girl")
        rt.prepare()
        fr = rt.seek(0)
        print(avatar, "->", rt.session.avatar_name, "bones", fr.bone_count, "ok", fr.finite)
    rt.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
