#!/usr/bin/env python3
"""M7 system benchmarks — full pipeline, cold/warm, memory."""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / "src"), str(REPO)]

from motion_engine.rendering.runtime import RuntimeFactory  # noqa: E402


def _report(name: str, samples_ns: list[int]) -> None:
    arr = [float(x) for x in samples_ns]
    print(
        f"{name:24s}  min={min(arr):.0f}  max={max(arr):.0f}  "
        f"mean={statistics.mean(arr):.0f}  median={statistics.median(arr):.0f}  "
        f"stdev={statistics.pstdev(arr):.0f}  p95={sorted(arr)[int(0.95*(len(arr)-1))]:.0f}  (ns)"
    )


def main() -> int:
    print("=== M7 System Benchmarks ===")

    # cold start
    t0 = time.perf_counter_ns()
    rt = RuntimeFactory().benchmark()
    rt.startup()
    rt.select_avatar("fixture")
    rt.select_mapping("test_two_bone")
    rt.prepare()
    cold_ns = time.perf_counter_ns() - t0
    print(f"cold_start_prepare       {cold_ns} ns")

    # 1000 frames
    samples = []
    for i in range(1000):
        t1 = time.perf_counter_ns()
        rt.seek(i)
        samples.append(time.perf_counter_ns() - t1)
    _report("pipeline_1000_frames", samples)

    # warm start second prepare
    t2 = time.perf_counter_ns()
    rt.prepare()
    warm_ns = time.perf_counter_ns() - t2
    print(f"warm_prepare             {warm_ns} ns")

    summary = rt.profiler_summary()
    print("memory_mb", summary.get("memory_mb"))
    print("fps_estimate", summary.get("fps_estimate"))
    rt.shutdown()
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
