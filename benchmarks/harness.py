"""Benchmark harness for the AXYX rendering architecture.

Run::

    python -m benchmarks.run_benchmarks

Or via pytest::

    pytest benchmarks/ -q
"""

from __future__ import annotations

import logging
import statistics
import time
import tracemalloc
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BenchmarkResult:
    """One named measurement."""

    name: str
    samples_ms: list[float] = field(default_factory=list)
    memory_peak_kib: float = 0.0
    extras: dict[str, Any] = field(default_factory=dict)

    @property
    def mean_ms(self) -> float:
        return statistics.fmean(self.samples_ms) if self.samples_ms else 0.0

    @property
    def min_ms(self) -> float:
        return min(self.samples_ms) if self.samples_ms else 0.0

    @property
    def max_ms(self) -> float:
        return max(self.samples_ms) if self.samples_ms else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "mean_ms": self.mean_ms,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
            "samples": len(self.samples_ms),
            "memory_peak_kib": self.memory_peak_kib,
            "extras": self.extras,
        }


@dataclass(slots=True)
class BenchmarkReport:
    """Full suite report."""

    results: list[BenchmarkResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"benchmarks": [r.to_dict() for r in self.results]}

    def summary_lines(self) -> list[str]:
        lines = ["AXYX rendering benchmarks"]
        for r in self.results:
            lines.append(
                f"  {r.name:32s}  mean={r.mean_ms:8.3f} ms  "
                f"min={r.min_ms:8.3f}  max={r.max_ms:8.3f}  "
                f"mem={r.memory_peak_kib:8.1f} KiB"
            )
        return lines


def _time_call(fn: Callable[[], Any], *, repeats: int) -> BenchmarkResult:
    name = getattr(fn, "__name__", "callable")
    samples: list[float] = []
    tracemalloc.start()
    peak = 0
    try:
        for _ in range(repeats):
            t0 = time.perf_counter_ns()
            fn()
            samples.append((time.perf_counter_ns() - t0) / 1_000_000.0)
            _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return BenchmarkResult(
        name=name,
        samples_ms=samples,
        memory_peak_kib=peak / 1024.0,
    )


def bench_resource_manager(repeats: int = 20) -> BenchmarkResult:
    from motion_engine.rendering.resources import ResourceManager

    def run() -> None:
        rm = ResourceManager()
        for i in range(50):
            rm.load("mesh", f"m{i}", factory=lambda i=i: {"i": i})
        rm.invalidate()

    run.__name__ = "resource_manager_load"
    return _time_call(run, repeats=repeats)


def bench_scene_graph(repeats: int = 20) -> BenchmarkResult:
    from motion_engine.rendering.scene import SceneGraph
    from motion_engine.rendering.scene.scene_node import RenderNode, TransformNode

    def run() -> None:
        g = SceneGraph()
        for i in range(100):
            parent = TransformNode(name=f"t{i}")
            g.add(parent)
            g.add(RenderNode(name=f"r{i}"), parent=parent)
        list(g.iter_render_nodes())

    run.__name__ = "scene_graph_create"
    return _time_call(run, repeats=repeats)


def bench_avatar_load(repeats: int = 20) -> BenchmarkResult:
    from motion_engine.rendering.avatar import AvatarManager, ProceduralAvatar
    from motion_engine.rendering.avatar.avatar_manifest import AvatarManifest

    def run() -> None:
        mgr = AvatarManager()
        avatar = ProceduralAvatar()
        mgr.register(avatar, make_active=True)
        avatar.load()
        AvatarManifest.procedural_default()

    run.__name__ = "avatar_load"
    return _time_call(run, repeats=repeats)


def bench_material_library(repeats: int = 50) -> BenchmarkResult:
    from motion_engine.rendering.materials import MaterialLibrary

    def run() -> None:
        lib = MaterialLibrary()
        for key in ("titanium", "graphite", "glass", "floor", "skin"):
            lib.get(key)

    run.__name__ = "material_library_get"
    return _time_call(run, repeats=repeats)


def bench_frame_context(repeats: int = 50) -> BenchmarkResult:
    from motion_engine.rendering.context import RenderSettings, RenderingContext
    from motion_engine.rendering.avatar import AvatarManager

    def run() -> None:
        ctx = RenderingContext(
            avatar_manager=AvatarManager(),
            settings=RenderSettings.defaults(),
        )
        for i in range(60):
            frame = ctx.make_frame(delta_time=1 / 60, viewport_width=1280, viewport_height=720)
            frame.metrics.apply_frame_time(1 / 60)

    run.__name__ = "frame_context_loop"
    return _time_call(run, repeats=repeats)


def bench_settings_and_presets(repeats: int = 30) -> BenchmarkResult:
    from motion_engine.rendering.camera import get_camera_profile
    from motion_engine.rendering.context import RenderSettings
    from motion_engine.rendering.environment import get_environment_preset
    from motion_engine.rendering.lighting.presets import get_lighting_preset
    from motion_engine.rendering.quality import get_quality

    def run() -> None:
        RenderSettings.load()
        get_quality("high")
        get_lighting_preset("studio")
        get_environment_preset("studio")
        get_camera_profile("clinical")

    run.__name__ = "settings_and_presets"
    return _time_call(run, repeats=repeats)


def bench_avatar_asset_pipeline(repeats: int = 10) -> BenchmarkResult:
    """Milestone 1 — manifest / mesh / full avatar load timings."""
    from motion_engine.rendering.avatar.loader import AvatarLoader, ManifestLoader, MeshLoader
    from motion_engine.rendering.assets import METAHUMAN_ROOT

    def run() -> None:
        ManifestLoader().load("avatar.procedural.default")
        ManifestLoader().load("metahuman")
        npz = METAHUMAN_ROOT / "cache" / "body_lod3.npz"
        if npz.is_file():
            MeshLoader().load_file(npz)
        AvatarLoader().load("avatar.metahuman.default", lod=3)

    run.__name__ = "avatar_asset_pipeline_m1"
    return _time_call(run, repeats=repeats)


def run_suite(*, repeats: int = 15) -> BenchmarkReport:
    """Run the full architecture benchmark suite (CPU-side, no GPU window)."""
    logger.info("Running rendering benchmark suite (repeats=%d)", repeats)
    report = BenchmarkReport(
        results=[
            bench_resource_manager(repeats=repeats),
            bench_scene_graph(repeats=repeats),
            bench_avatar_load(repeats=repeats),
            bench_material_library(repeats=max(repeats, 30)),
            bench_frame_context(repeats=max(repeats, 30)),
            bench_settings_and_presets(repeats=repeats),
            bench_avatar_asset_pipeline(repeats=max(3, repeats // 2)),
        ]
    )
    for line in report.summary_lines():
        logger.info("%s", line)
    return report


__all__ = [
    "BenchmarkResult",
    "BenchmarkReport",
    "run_suite",
    "bench_resource_manager",
    "bench_scene_graph",
    "bench_avatar_load",
    "bench_material_library",
    "bench_frame_context",
    "bench_settings_and_presets",
    "bench_avatar_asset_pipeline",
]
