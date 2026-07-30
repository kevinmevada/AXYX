#!/usr/bin/env python3
"""Multiple subjects batch walkthrough."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / "src"), str(REPO)]

from motion_engine.rendering.runtime import RuntimeFactory  # noqa: E402


def main() -> int:
    rt = RuntimeFactory().debug()
    rt.startup()
    rt.select_avatar("fixture")
    rt.select_mapping("test_two_bone")
    for subject in ("S1", "S2", "S3"):
        for trial in ("WU01", "WU02"):
            rt.select_subject(subject)
            rt.select_trial(trial)
            rt.prepare()
            frames = rt.run_frames(5)
            print(subject, trial, "ok", all(f.finite for f in frames))
    rt.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
