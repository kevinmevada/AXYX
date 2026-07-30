#!/usr/bin/env python3
"""M5 Animation Runtime micro-benchmarks."""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / "src"), str(REPO)]

from motion_engine.rendering.avatar.animation import (  # noqa: E402
    AnimationController,
    AnimationFactory,
    AnimationPlayer,
    AnimationState,
    ControllerState,
    LoopMode,
    Transition,
    blend_poses,
    quat_slerp,
)
from tests.skinning.helpers import make_bind  # noqa: E402

N = 100


def _stats(samples_ns: list[int]) -> dict[str, float]:
    arr = [s / 1e6 for s in samples_ns]  # ms
    arr_sorted = sorted(arr)
    p95 = arr_sorted[int(0.95 * (len(arr_sorted) - 1))]
    return {
        "min": min(arr),
        "max": max(arr),
        "mean": statistics.mean(arr),
        "median": statistics.median(arr),
        "stdev": statistics.pstdev(arr) if len(arr) > 1 else 0.0,
        "p95": p95,
    }


def bench(name: str, fn) -> None:
    samples = []
    for _ in range(N):
        t0 = time.perf_counter_ns()
        fn()
        samples.append(time.perf_counter_ns() - t0)
    st = _stats(samples)
    print(
        f"{name:24s}  mean={st['mean']:.4f}ms  med={st['median']:.4f}ms  "
        f"p95={st['p95']:.4f}ms  min={st['min']:.4f} max={st['max']:.4f}  stdev={st['stdev']:.4f}"
    )


def main() -> int:
    bind = make_bind()
    factory = AnimationFactory()
    clip = factory.wave_clip(bind, "forearm", duration=1.0)
    player = AnimationPlayer(bind=bind)
    player.load(clip)
    player.play()
    a = player.seek(0.0)
    b = player.seek(0.5)

    print(f"M5 animation benchmarks  N={N}")
    bench("sampling", lambda: player.evaluator.sampler.sample(clip, 0.33))
    bench("interpolation_slerp", lambda: quat_slerp((0, 0, 0, 1), (0, 0, 0.7071, 0.7071), 0.5))
    bench("playback_tick", lambda: player.tick(1.0 / 60.0))
    ctrl = AnimationController(bind=bind)
    clips = factory.locomotion_set(bind, "forearm")
    ctrl.add_state(AnimationState("idle", ControllerState.IDLE, clips["idle"]))
    ctrl.add_state(AnimationState("walk", ControllerState.WALK, clips["walk"]))
    ctrl.add_transition(Transition("idle", "walk", 0.1))
    ctrl.set_state("idle")

    def _ctrl():
        ctrl.set_state("walk", fade=0.1)
        ctrl.tick(1.0 / 60.0)

    bench("controller", _ctrl)
    bench("blending", lambda: blend_poses(a, b, 0.5))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
