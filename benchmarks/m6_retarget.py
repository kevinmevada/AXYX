#!/usr/bin/env python3
"""M6 retarget benchmarks — mapping, conversion, retarget, constraints, filters."""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / "src"), str(REPO)]

from motion_engine.rendering.avatar.retarget.constraint_solver import ConstraintSolver  # noqa: E402
from motion_engine.rendering.avatar.retarget.factory import RetargetFactory  # noqa: E402
from motion_engine.rendering.avatar.retarget.filters import MovingAverageFilter  # noqa: E402
from motion_engine.rendering.avatar.retarget.mapping_factory import MappingFactory  # noqa: E402
from motion_engine.rendering.avatar.retarget.motion_converter import MotionConverter  # noqa: E402
from motion_engine.rendering.avatar.retarget.types import JointLimit  # noqa: E402
from tests.retarget.helpers import flexed_pose, two_bone_setup  # noqa: E402

N = 100


def _report(name: str, samples_ns: list[int]) -> None:
    arr = [float(x) for x in samples_ns]
    print(
        f"{name:24s}  min={min(arr):.0f}  max={max(arr):.0f}  "
        f"mean={statistics.mean(arr):.0f}  median={statistics.median(arr):.0f}  "
        f"stdev={statistics.pstdev(arr):.0f}  p95={sorted(arr)[int(0.95*(len(arr)-1))]:.0f}  (ns)"
    )


def bench(fn, n: int = N) -> list[int]:
    # warmup
    for _ in range(5):
        fn()
    out = []
    for _ in range(n):
        t0 = time.perf_counter_ns()
        fn()
        out.append(time.perf_counter_ns() - t0)
    return out


def main() -> int:
    print("=== M6 Retarget Benchmarks ===")
    factory = MappingFactory()
    _report("mapping_builtin", bench(lambda: factory.builtin("matlab_clinical_to_army_girl")))

    conv = MotionConverter()
    skel = RetargetFactory().clinical_skeleton()
    _report(
        "conversion_gait_frame",
        bench(lambda: next(iter(conv.iter_gait(skel, n_frames=1)))),
    )

    engine, ctx, *_ = two_bone_setup()
    pose = flexed_pose(30.0)
    _report("retarget_frame", bench(lambda: engine.retarget(pose, ctx)))

    cs = ConstraintSolver([JointLimit(bone="forearm", min_xyz=(-1, -1, -1), max_xyz=(1, 1, 1))])
    q = pose.joints["forearm"].rotation_xyzw
    _report("constraint_solve", bench(lambda: cs.apply({"forearm": q})))

    filt = MovingAverageFilter(5)
    _report("filter_ma_quat", bench(lambda: filt.push_quat("forearm", q)))

    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
