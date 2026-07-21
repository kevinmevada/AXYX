#!/usr/bin/env python3
"""M4 skinning benchmarks."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / "src"), str(REPO)]

from benchmarks.timing import TimingStats, benchmark  # noqa: E402
from motion_engine.rendering.avatar.skinning import (  # noqa: E402
    SkinningRuntime,
    build_matrix_palette,
    normalize_weights,
    validate_weight_table,
)
from tests.skinning.helpers import make_bind, make_mesh_skin, make_segment_mesh  # noqa: E402


@dataclass
class Report:
    created_utc: str
    iterations: int
    environment: dict[str, Any]
    metrics: list[dict[str, Any]] = field(default_factory=list)

    def add(self, s: TimingStats) -> None:
        self.metrics.append(s.to_dict())


def run_suite(iterations: int = 100, warmup: int = 2) -> Report:
    report = Report(
        created_utc=datetime.now(timezone.utc).isoformat(),
        iterations=iterations,
        environment={"python": sys.version.split()[0], "platform": platform.platform()},
    )
    mesh = make_segment_mesh(256)
    skin = make_mesh_skin(mesh)
    bind = make_bind()
    rt = SkinningRuntime()

    report.add(
        benchmark(
            "matrix_palette",
            lambda: build_matrix_palette(bind),
            iterations=iterations,
            warmup=warmup,
        )
    )
    report.add(
        benchmark(
            "weight_normalization",
            lambda: normalize_weights(skin.weight_table),
            iterations=iterations,
            warmup=warmup,
        )
    )
    report.add(
        benchmark(
            "cpu_skinning",
            lambda: rt.deform(mesh, skin, bind_pose=bind),
            iterations=iterations,
            warmup=warmup,
        )
    )
    report.add(
        benchmark(
            "validation",
            lambda: validate_weight_table(skin.weight_table, bone_count=2, vertex_count=mesh.vertex_count),
            iterations=iterations,
            warmup=warmup,
        )
    )
    cache_rt = SkinningRuntime(cache=__import__(
        "motion_engine.rendering.avatar.skinning", fromlist=["SkinningCache"]
    ).SkinningCache())
    report.add(
        benchmark(
            "cache_hit_path",
            lambda: cache_rt.deform(mesh, skin, bind_pose=bind, cache_key="k"),
            iterations=iterations,
            warmup=warmup,
        )
    )
    return report


def export(report: Report, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "m4_skinning.json").write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
    with (out / "m4_skinning.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=["name", "n", "min_ms", "max_ms", "mean_ms", "median_ms", "stdev_ms", "p95_ms"],
        )
        w.writeheader()
        for m in report.metrics:
            w.writerow({k: m[k] for k in w.fieldnames})
    lines = ["# M4 Skinning Benchmarks", "", "| Metric | Mean | P95 |", "|--------|------|-----|"]
    for m in report.metrics:
        lines.append(f"| `{m['name']}` | {m['mean_ms']:.4f} | {m['p95_ms']:.4f} |")
    (out / "m4_skinning.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--iterations", type=int, default=100)
    p.add_argument("--out", type=Path, default=REPO / "benchmarks" / "results")
    args = p.parse_args(argv)
    report = run_suite(args.iterations)
    export(report, args.out)
    print(f"Wrote M4 benchmarks to {args.out}")
    for m in report.metrics:
        print(f"  {m['name']}: mean={m['mean_ms']:.4f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
