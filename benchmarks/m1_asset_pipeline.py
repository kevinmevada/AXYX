"""Research-grade Milestone 1 asset-pipeline benchmarks.

Isolated from production loaders — instruments public APIs and local
re-creation of load steps using ``time.perf_counter_ns()``.

Run::

    python -m benchmarks.m1_asset_pipeline
    python -m benchmarks.m1_asset_pipeline --iterations 50 --out benchmarks/results
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

# Repo bootstrap when executed as ``python -m benchmarks.m1_asset_pipeline``
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from benchmarks.timing import TimingStats, benchmark, ns_to_ms, time_call_ns

logger = logging.getLogger("axyx.bench.m1")


@dataclass
class M1BenchmarkReport:
    """Full Milestone 1 benchmark report."""

    created_utc: str
    iterations: int
    warmup: int
    metrics: list[TimingStats] = field(default_factory=list)
    footprint: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)

    def metric(self, name: str) -> TimingStats | None:
        for m in self.metrics:
            if m.name == name:
                return m
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "created_utc": self.created_utc,
            "iterations": self.iterations,
            "warmup": self.warmup,
            "environment": self.environment,
            "footprint": self.footprint,
            "metrics": [m.to_dict() for m in self.metrics],
        }


def _env() -> dict[str, Any]:
    import platform

    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "executable": sys.executable,
    }


def _loaded_avatar_footprint(loaded: Any) -> dict[str, Any]:
    """Estimate resident array footprint of a LoadedAvatar (bytes)."""

    def _nbytes(obj: Any) -> int:
        if obj is None:
            return 0
        if isinstance(obj, np.ndarray):
            return int(obj.nbytes)
        return 0

    mesh = loaded.primary_mesh
    mesh_bytes = 0
    if mesh is not None:
        mesh_bytes = (
            _nbytes(mesh.positions)
            + _nbytes(mesh.normals)
            + _nbytes(mesh.uvs)
            + _nbytes(mesh.indices)
            + _nbytes(mesh.joint_indices)
            + _nbytes(mesh.joint_weights)
        )
    tex_bytes = sum(_nbytes(t.data) for t in loaded.textures)
    skel_bytes = 0
    if loaded.skeleton is not None:
        for b in loaded.skeleton.bones:
            skel_bytes += _nbytes(b.bind_world) + _nbytes(b.inverse_bind)
    total = mesh_bytes + tex_bytes + skel_bytes
    return {
        "mesh_bytes": mesh_bytes,
        "texture_bytes": tex_bytes,
        "skeleton_bytes": skel_bytes,
        "total_bytes": total,
        "total_mib": total / (1024.0 * 1024.0),
        "vertex_count": mesh.vertex_count if mesh else 0,
        "triangle_count": mesh.triangle_count if mesh else 0,
        "bone_count": loaded.skeleton.bone_count if loaded.skeleton else 0,
        "material_count": len(loaded.materials),
        "texture_count": len(loaded.textures),
        "avatar_id": loaded.id,
    }


def run_m1_benchmarks(
    *,
    iterations: int = 100,
    warmup: int = 1,
    lod: int = 3,
    avatar_id: str = "avatar.metahuman.default",
) -> M1BenchmarkReport:
    """Execute the full M1 asset-pipeline benchmark suite.

    Cold and warm avatar loads are measured separately and never averaged.
    """
    from motion_engine.rendering.assets import METAHUMAN_ROOT
    from motion_engine.rendering.avatar.loader import (
        AvatarLoader,
        ManifestLoader,
        MaterialLoader,
        MeshLoader,
        SkeletonLoader,
        TextureLoader,
    )
    from motion_engine.rendering.avatar.loader.mesh_formats import NpzMeshHandler
    from motion_engine.rendering.avatar.loader.path_utils import resolve_manifest_path
    from motion_engine.rendering.avatar.models.mesh import compute_bounds
    from motion_engine.rendering.avatar.registry import AvatarRegistry
    from motion_engine.rendering.avatar.validation import ManifestValidator
    import json

    report = M1BenchmarkReport(
        created_utc=datetime.now(timezone.utc).isoformat(),
        iterations=iterations,
        warmup=warmup,
        environment=_env(),
    )
    metrics: list[TimingStats] = []

    # ----- Resolve paths once (not timed as suite setup) -----
    manifest_path = resolve_manifest_path(avatar_id)
    mesh_path = METAHUMAN_ROOT / "cache" / f"body_lod{lod}.npz"
    tex_path = METAHUMAN_ROOT / "cache" / "textures" / "body_bc.png"
    if not mesh_path.is_file():
        raise FileNotFoundError(f"Benchmark mesh missing: {mesh_path}")

    validator = ManifestValidator()
    manifest_loader = ManifestLoader(validator=validator)

    # ========== Manifest breakdown ==========
    def path_resolution() -> None:
        resolve_manifest_path(avatar_id)

    metrics.append(
        benchmark(
            "manifest_path_resolution",
            path_resolution,
            iterations=iterations,
            warmup=warmup,
        )
    )

    def parse() -> dict[str, Any]:
        text = manifest_path.read_text(encoding="utf-8")
        return json.loads(text)

    metrics.append(
        benchmark("manifest_parse", parse, iterations=iterations, warmup=warmup)
    )

    raw_once = parse()

    def validate() -> None:
        validator.validate(raw_once, source=str(manifest_path))

    metrics.append(
        benchmark(
            "manifest_validation", validate, iterations=iterations, warmup=warmup
        )
    )

    metrics.append(
        benchmark(
            "manifest_load_total",
            lambda: manifest_loader.load(avatar_id),
            iterations=max(10, iterations // 5),
            warmup=warmup,
        )
    )

    # ========== Mesh breakdown ==========
    handler = NpzMeshHandler()

    def mesh_file_read() -> bytes:
        return mesh_path.read_bytes()

    metrics.append(
        benchmark(
            "mesh_file_read",
            mesh_file_read,
            iterations=max(20, iterations // 2),
            warmup=warmup,
        )
    )

    def mesh_decode() -> Any:
        return np.load(mesh_path, allow_pickle=True)

    metrics.append(
        benchmark(
            "mesh_decode",
            mesh_decode,
            iterations=max(20, iterations // 2),
            warmup=warmup,
        )
    )

    decoded = np.load(mesh_path, allow_pickle=True)

    def mesh_vertex_extract() -> np.ndarray:
        return np.asarray(decoded["positions"], dtype=np.float32).copy()

    def mesh_index_extract() -> np.ndarray:
        faces = np.asarray(decoded["faces"], dtype=np.int32)
        return faces.reshape(-1).copy()

    metrics.append(
        benchmark(
            "mesh_vertex_extraction",
            mesh_vertex_extract,
            iterations=iterations,
            warmup=warmup,
        )
    )
    metrics.append(
        benchmark(
            "mesh_index_extraction",
            mesh_index_extract,
            iterations=iterations,
            warmup=warmup,
        )
    )

    positions = np.asarray(decoded["positions"], dtype=np.float32)

    def mesh_bounds() -> None:
        compute_bounds(positions)

    metrics.append(
        benchmark(
            "mesh_bounding_volume",
            mesh_bounds,
            iterations=iterations,
            warmup=warmup,
        )
    )

    metrics.append(
        benchmark(
            "mesh_load_total",
            lambda: handler.load(mesh_path),
            iterations=max(20, iterations // 2),
            warmup=warmup,
        )
    )

    # ========== Skeleton ==========
    manifest = manifest_loader.load(avatar_id)
    skel_loader = SkeletonLoader()

    def skeleton_load() -> None:
        skel_loader.load_from_manifest(manifest)

    # Hierarchy / bone parsing / transforms are inside load_from_manifest;
    # measure full load + NPZ-only path for hierarchy creation timing.
    metrics.append(
        benchmark(
            "skeleton_load_total",
            skeleton_load,
            iterations=max(20, iterations // 2),
            warmup=warmup,
        )
    )

    hierarchy = manifest.root / str(
        dict(manifest.skeleton).get("hierarchy_cache", "cache/skeleton.json")
    )

    def skeleton_hierarchy() -> None:
        skel_loader.load_json_hierarchy(hierarchy)

    if hierarchy.is_file():
        metrics.append(
            benchmark(
                "skeleton_hierarchy_creation",
                skeleton_hierarchy,
                iterations=max(20, iterations // 2),
                warmup=warmup,
            )
        )

    def skeleton_npz_bones() -> None:
        skel_loader.load_from_npz(mesh_path, hierarchy_json=hierarchy if hierarchy.is_file() else None)

    metrics.append(
        benchmark(
            "skeleton_bone_parsing",
            skeleton_npz_bones,
            iterations=max(10, iterations // 5),
            warmup=warmup,
        )
    )

    # Transform generation ≈ loading bind_world / IBM from NPZ (included above);
    # explicit matrix copy timing:
    inv = np.asarray(decoded["inv_bind"], dtype=np.float64)

    def skeleton_transform_generation() -> np.ndarray:
        return inv.copy()

    metrics.append(
        benchmark(
            "skeleton_transform_generation",
            skeleton_transform_generation,
            iterations=iterations,
            warmup=warmup,
        )
    )

    # ========== Textures ==========
    tex_loader = TextureLoader()
    if tex_path.is_file():

        def texture_disk_io() -> bytes:
            return tex_path.read_bytes()

        metrics.append(
            benchmark(
                "texture_disk_io",
                texture_disk_io,
                iterations=max(20, iterations // 2),
                warmup=warmup,
            )
        )

        def texture_decode() -> None:
            tex_loader.load_file(tex_path, name="bc", slot="albedo")

        metrics.append(
            benchmark(
                "texture_decode",
                texture_decode,
                iterations=max(10, iterations // 5),
                warmup=warmup,
            )
        )
        # CPU path only — no GPU upload in M1 pipeline
        metrics.append(
            TimingStats(
                name="texture_gpu_preparation",
                samples_ms=[0.0],
                extras={"note": "N/A — M1 CPU bind-pose path (no GPU upload)"},
            )
        )

    # ========== Materials ==========
    mat_loader = MaterialLoader(texture_loader=tex_loader)

    def material_build() -> None:
        # Use a fresh loader to avoid accidental caching side effects
        MaterialLoader(texture_loader=TextureLoader()).load_from_manifest(manifest)

    # Material construction includes texture binding for metahuman — expensive.
    # Separate "creation" vs "binding" by using procedural (presets only) vs metahuman.
    from motion_engine.rendering.avatar.loader import ManifestLoader as ML

    proc = ML().load("procedural")

    def material_creation_presets() -> None:
        MaterialLoader().load_from_manifest(proc)

    metrics.append(
        benchmark(
            "material_creation",
            material_creation_presets,
            iterations=iterations,
            warmup=warmup,
        )
    )

    metrics.append(
        benchmark(
            "material_texture_binding",
            material_build,
            iterations=max(5, iterations // 20),
            warmup=max(1, warmup),
            track_memory=True,
        )
    )

    # ========== Avatar construction pipeline (instrumented stages) ==========
    # Single-pass staged timing (mean over fewer iterations — disk heavy)
    stage_iters = max(5, min(20, iterations // 10))
    stage_names = (
        "avatar_stage_manifest",
        "avatar_stage_mesh",
        "avatar_stage_skeleton",
        "avatar_stage_textures_materials",
        "avatar_stage_validation",
        "avatar_construction_total",
    )
    stage_samples: dict[str, list[float]] = {n: [] for n in stage_names}

    from motion_engine.rendering.avatar.validation import AssetValidator
    from motion_engine.rendering.avatar.models.avatar import LoadedAvatar

    mesh_loader = MeshLoader()
    for _ in range(warmup):
        AvatarLoader().load(avatar_id, lod=lod)

    for _ in range(stage_iters):
        t_all = time.perf_counter_ns()

        t0 = time.perf_counter_ns()
        man = ManifestLoader().load(avatar_id)
        stage_samples["avatar_stage_manifest"].append(ns_to_ms(time.perf_counter_ns() - t0))

        t0 = time.perf_counter_ns()
        meshes = mesh_loader.load_from_manifest(man, lod=lod)
        stage_samples["avatar_stage_mesh"].append(ns_to_ms(time.perf_counter_ns() - t0))

        t0 = time.perf_counter_ns()
        skeleton = SkeletonLoader().load_from_manifest(man)
        stage_samples["avatar_stage_skeleton"].append(ns_to_ms(time.perf_counter_ns() - t0))

        t0 = time.perf_counter_ns()
        materials, textures = MaterialLoader().load_from_manifest(man)
        stage_samples["avatar_stage_textures_materials"].append(
            ns_to_ms(time.perf_counter_ns() - t0)
        )

        loaded = LoadedAvatar(
            id=man.asset_id,
            manifest=man,
            meshes=meshes,
            materials=materials,
            skeleton=skeleton,
            textures=textures,
            metadata={},
        )
        t0 = time.perf_counter_ns()
        AssetValidator().validate(loaded)
        stage_samples["avatar_stage_validation"].append(
            ns_to_ms(time.perf_counter_ns() - t0)
        )

        stage_samples["avatar_construction_total"].append(
            ns_to_ms(time.perf_counter_ns() - t_all)
        )

    for name, samples in stage_samples.items():
        metrics.append(TimingStats(name=name, samples_ms=samples))

    # ========== Cold vs Warm (separate — never averaged) ==========
    # Cold: process-fresh loader, first disk load (single sample + few repeats of "cold-ish")
    cold_samples: list[float] = []
    for i in range(max(3, min(10, iterations // 20))):
        loader = AvatarLoader()  # new instance
        _, elapsed = time_call_ns(lambda: loader.load(avatar_id, lod=lod))
        cold_samples.append(ns_to_ms(elapsed))
    metrics.append(
        TimingStats(
            name="cold_avatar_load",
            samples_ms=cold_samples,
            extras={"note": "Separate from warm; new AvatarLoader each sample"},
        )
    )

    warm_loader = AvatarLoader()
    warm_loader.load(avatar_id, lod=lod)  # prime OS page cache / decoder

    def warm() -> None:
        warm_loader.load(avatar_id, lod=lod)

    metrics.append(
        benchmark(
            "warm_avatar_load",
            warm,
            iterations=max(5, min(30, iterations // 5)),
            warmup=1,
            track_memory=True,
        )
    )

    # ========== Registry ==========
    reg = AvatarRegistry()
    triangle = _ROOT / "tests" / "fixtures" / "avatars" / "triangle" / "avatar.json"

    def registry_register() -> None:
        reg.register(f"bench.tmp.{time.perf_counter_ns()}", triangle, replace=True)

    # register with unique ids — measure path only
    reg2 = AvatarRegistry()

    def reg_register_fixed() -> None:
        reg2.register("bench.fixed", triangle, replace=True)

    metrics.append(
        benchmark(
            "registry_register",
            reg_register_fixed,
            iterations=iterations,
            warmup=warmup,
        )
    )

    reg2.register("bench.lookup", triangle, replace=True)
    reg2.get("bench.lookup")  # populate cache

    def registry_lookup_hit() -> None:
        reg2.get("bench.lookup")

    metrics.append(
        benchmark(
            "registry_lookup_cache_hit",
            registry_lookup_hit,
            iterations=iterations,
            warmup=warmup,
        )
    )

    def registry_lookup_miss_load() -> None:
        reg2.invalidate("bench.lookup")
        reg2.get("bench.lookup")

    metrics.append(
        benchmark(
            "registry_lookup_cache_miss",
            registry_lookup_miss_load,
            iterations=max(5, iterations // 20),
            warmup=1,
        )
    )

    def registry_reload() -> None:
        reg2.reload("bench.lookup")

    metrics.append(
        benchmark(
            "registry_reload",
            registry_reload,
            iterations=max(5, iterations // 20),
            warmup=1,
        )
    )

    # ========== Footprint ==========
    final = AvatarLoader().load(avatar_id, lod=lod)
    report.footprint = _loaded_avatar_footprint(final)
    report.metrics = metrics
    return report


# ----- Reporting -----

_DISPLAY_ORDER = [
    ("manifest_parse", "Manifest Parse"),
    ("manifest_validation", "Manifest Validation"),
    ("manifest_path_resolution", "Manifest Path Resolution"),
    ("mesh_file_read", "Mesh File Read"),
    ("mesh_decode", "Mesh Decode"),
    ("mesh_vertex_extraction", "Mesh Vertex Extraction"),
    ("mesh_index_extraction", "Mesh Index Extraction"),
    ("mesh_bounding_volume", "Mesh Bounding Volume"),
    ("mesh_load_total", "Mesh Load"),
    ("skeleton_hierarchy_creation", "Skeleton Hierarchy"),
    ("skeleton_bone_parsing", "Skeleton Bone Parsing"),
    ("skeleton_transform_generation", "Skeleton Transform Generation"),
    ("skeleton_load_total", "Skeleton Load"),
    ("texture_disk_io", "Texture Disk IO"),
    ("texture_decode", "Texture Decode"),
    ("texture_gpu_preparation", "Texture GPU Preparation"),
    ("material_creation", "Material Creation"),
    ("material_texture_binding", "Material Texture Binding"),
    ("avatar_stage_manifest", "Avatar Stage: Manifest"),
    ("avatar_stage_mesh", "Avatar Stage: Mesh"),
    ("avatar_stage_skeleton", "Avatar Stage: Skeleton"),
    ("avatar_stage_textures_materials", "Avatar Stage: Textures+Materials"),
    ("avatar_stage_validation", "Avatar Stage: Validation"),
    ("avatar_construction_total", "Avatar Construction"),
    ("registry_register", "Registry Register"),
    ("registry_lookup_cache_hit", "Registry Lookup (cache hit)"),
    ("registry_lookup_cache_miss", "Registry Lookup (cache miss)"),
    ("registry_reload", "Registry Reload"),
    ("warm_avatar_load", "Warm Avatar Load"),
    ("cold_avatar_load", "Cold Avatar Load"),
]


def format_table(report: M1BenchmarkReport) -> str:
    """ASCII research-grade summary table (means)."""
    by_name = {m.name: m for m in report.metrics}
    lines = [
        "-" * 55,
        "AXYX M1 Asset Pipeline Benchmark",
        "-" * 55,
    ]
    width = max(len(label) for _, label in _DISPLAY_ORDER)
    for key, label in _DISPLAY_ORDER:
        m = by_name.get(key)
        if m is None:
            continue
        lines.append(f"{label + ' ':.<{width + 2}} {m.format_mean()}")
    lines.append("-" * 55)
    lines.append("Statistics (per metric: min / median / mean / max / stdev / p95)")
    lines.append("-" * 55)
    for key, label in _DISPLAY_ORDER:
        m = by_name.get(key)
        if m is None or m.n == 0:
            continue
        lines.append(
            f"{label}: "
            f"min={m.min_ms:.4f} med={m.median_ms:.4f} mean={m.mean_ms:.4f} "
            f"max={m.max_ms:.4f} std={m.stdev_ms:.4f} p95={m.p95_ms:.4f} ms "
            f"(n={m.n})"
        )
    lines.append("-" * 55)
    fp = report.footprint
    if fp:
        lines.append(
            f"LoadedAvatar footprint: {fp.get('total_mib', 0):.2f} MiB "
            f"(mesh={fp.get('mesh_bytes', 0)} B, tex={fp.get('texture_bytes', 0)} B, "
            f"skel={fp.get('skeleton_bytes', 0)} B)"
        )
        lines.append(
            f"Geometry: V={fp.get('vertex_count')} T={fp.get('triangle_count')} "
            f"bones={fp.get('bone_count')} mats={fp.get('material_count')} "
            f"tex={fp.get('texture_count')}"
        )
    lines.append("-" * 55)
    return "\n".join(lines)


def write_markdown(report: M1BenchmarkReport, path: Path) -> None:
    """Write a Markdown benchmark report."""
    by_name = {m.name: m for m in report.metrics}
    lines = [
        "# AXYX M1 Asset Pipeline Benchmark",
        "",
        f"- Created (UTC): `{report.created_utc}`",
        f"- Iterations: **{report.iterations}** (warmup **{report.warmup}**)",
        f"- Python: `{report.environment.get('python')}`",
        f"- Platform: `{report.environment.get('platform')}`",
        "",
        "## Summary (mean)",
        "",
        "| Metric | Mean | Median | Min | Max | Std Dev | P95 | N |",
        "|--------|------|--------|-----|-----|---------|-----|---|",
    ]
    for key, label in _DISPLAY_ORDER:
        m = by_name.get(key)
        if m is None:
            continue
        lines.append(
            f"| {label} | {m.mean_ms:.4f} ms | {m.median_ms:.4f} ms | "
            f"{m.min_ms:.4f} ms | {m.max_ms:.4f} ms | {m.stdev_ms:.4f} ms | "
            f"{m.p95_ms:.4f} ms | {m.n} |"
        )
    lines.extend(["", "## Cold vs Warm", ""])
    cold = by_name.get("cold_avatar_load")
    warm = by_name.get("warm_avatar_load")
    if cold:
        lines.append(
            f"- **Cold** mean `{cold.mean_ms:.3f} ms` "
            f"(min {cold.min_ms:.3f}, max {cold.max_ms:.3f}, n={cold.n})"
        )
    if warm:
        lines.append(
            f"- **Warm** mean `{warm.mean_ms:.3f} ms` "
            f"(min {warm.min_ms:.3f}, max {warm.max_ms:.3f}, n={warm.n})"
        )
    lines.append("")
    lines.append("> Cold and warm are measured separately and never averaged together.")
    fp = report.footprint
    if fp:
        lines.extend(
            [
                "",
                "## Memory footprint (LoadedAvatar arrays)",
                "",
                f"- Total: **{fp.get('total_mib', 0):.3f} MiB**",
                f"- Mesh: {fp.get('mesh_bytes', 0)} bytes",
                f"- Textures: {fp.get('texture_bytes', 0)} bytes",
                f"- Skeleton: {fp.get('skeleton_bytes', 0)} bytes",
            ]
        )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(report: M1BenchmarkReport, path: Path) -> None:
    """Export metrics as CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "name",
                "n",
                "min_ms",
                "max_ms",
                "mean_ms",
                "median_ms",
                "stdev_ms",
                "p95_ms",
                "memory_peak_kib",
            ],
        )
        writer.writeheader()
        for m in report.metrics:
            writer.writerow(
                {
                    "name": m.name,
                    "n": m.n,
                    "min_ms": f"{m.min_ms:.6f}",
                    "max_ms": f"{m.max_ms:.6f}",
                    "mean_ms": f"{m.mean_ms:.6f}",
                    "median_ms": f"{m.median_ms:.6f}",
                    "stdev_ms": f"{m.stdev_ms:.6f}",
                    "p95_ms": f"{m.p95_ms:.6f}",
                    "memory_peak_kib": f"{m.memory_peak_kib:.3f}",
                }
            )


def write_json(report: M1BenchmarkReport, path: Path) -> None:
    """Export full report as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AXYX M1 research-grade benchmarks")
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--lod", type=int, default=3)
    parser.add_argument(
        "--out",
        type=Path,
        default=_ROOT / "benchmarks" / "results",
        help="Output directory for md/csv/json",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(message)s",
    )

    print("Running AXYX M1 asset pipeline benchmarks...")
    t0 = time.perf_counter_ns()
    report = run_m1_benchmarks(
        iterations=args.iterations, warmup=args.warmup, lod=args.lod
    )
    elapsed = ns_to_ms(time.perf_counter_ns() - t0)
    print(format_table(report))
    print(f"Suite wall time: {elapsed:.1f} ms")

    out: Path = args.out
    write_markdown(report, out / "m1_asset_pipeline.md")
    write_csv(report, out / "m1_asset_pipeline.csv")
    write_json(report, out / "m1_asset_pipeline.json")
    print(f"Wrote: {out / 'm1_asset_pipeline.md'}")
    print(f"Wrote: {out / 'm1_asset_pipeline.csv'}")
    print(f"Wrote: {out / 'm1_asset_pipeline.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
