#!/usr/bin/env python3
"""AXYX Phase 1 — Milestone 2 Avatar Skeleton benchmarks.

Uses ``time.perf_counter_ns()`` via :mod:`benchmarks.timing`.

Run::

    python -m benchmarks.m2_avatar_skeleton --iterations 100
"""

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

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from benchmarks.timing import TimingStats, benchmark  # noqa: E402
from motion_engine.rendering.avatar.skeleton import (  # noqa: E402
    AvatarSkeletonFactory,
    export_json,
    export_tree,
)
from tests.skeleton.helpers import make_chain_imported, make_tree_imported  # noqa: E402


@dataclass
class M2BenchmarkReport:
    """Aggregate M2 benchmark results."""

    created_utc: str
    iterations: int
    environment: dict[str, Any]
    metrics: list[dict[str, Any]] = field(default_factory=list)

    def add(self, stats: TimingStats) -> None:
        self.metrics.append(stats.to_dict())


def _env() -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
    }


def run_suite(iterations: int = 100, warmup: int = 2) -> M2BenchmarkReport:
    """Execute the M2 skeleton benchmark suite."""
    report = M2BenchmarkReport(
        created_utc=datetime.now(timezone.utc).isoformat(),
        iterations=iterations,
        environment=_env(),
    )
    factory = AvatarSkeletonFactory()
    imported_chain = make_chain_imported(128)
    imported_tree = make_tree_imported()
    runtime = factory.from_imported(imported_chain)

    report.add(
        benchmark(
            "construction_from_imported",
            lambda: factory.from_imported(imported_chain),
            iterations=iterations,
            warmup=warmup,
        )
    )
    report.add(
        benchmark(
            "construction_tree",
            lambda: factory.from_imported(imported_tree),
            iterations=iterations,
            warmup=warmup,
        )
    )
    report.add(
        benchmark(
            "validation",
            lambda: runtime.validate(),
            iterations=iterations,
            warmup=warmup,
        )
    )
    report.add(
        benchmark(
            "lookup_by_name",
            lambda: runtime.find("b64"),
            iterations=iterations,
            warmup=warmup,
        )
    )
    report.add(
        benchmark(
            "traversal_dfs",
            lambda: list(runtime.traversal.dfs()),
            iterations=iterations,
            warmup=warmup,
        )
    )
    report.add(
        benchmark(
            "traversal_bfs",
            lambda: list(runtime.traversal.bfs()),
            iterations=iterations,
            warmup=warmup,
        )
    )
    report.add(
        benchmark(
            "transform_propagation",
            lambda: runtime.rebuild_world_rest(),
            iterations=iterations,
            warmup=warmup,
        )
    )
    report.add(
        benchmark(
            "statistics_access",
            lambda: runtime.statistics.to_dict(),
            iterations=iterations,
            warmup=warmup,
        )
    )
    report.add(
        benchmark(
            "serialization_json",
            lambda: export_json(runtime),
            iterations=max(10, iterations // 5),
            warmup=warmup,
        )
    )
    report.add(
        benchmark(
            "serialization_tree",
            lambda: export_tree(runtime),
            iterations=iterations,
            warmup=warmup,
        )
    )
    return report


def export_report(report: M2BenchmarkReport, out_dir: Path) -> None:
    """Write markdown / CSV / JSON artifacts."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "m2_avatar_skeleton.json"
    csv_path = out_dir / "m2_avatar_skeleton.csv"
    md_path = out_dir / "m2_avatar_skeleton.md"

    json_path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as fh:
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
            ],
        )
        writer.writeheader()
        for m in report.metrics:
            writer.writerow({k: m[k] for k in writer.fieldnames})

    lines = [
        "# M2 Avatar Skeleton Benchmarks",
        "",
        f"- Created: `{report.created_utc}`",
        f"- Iterations: `{report.iterations}`",
        f"- Platform: `{report.environment.get('platform')}`",
        "",
        "| Metric | Mean | Median | P95 | Min | Max | Stdev |",
        "|--------|------|--------|-----|-----|-----|-------|",
    ]
    for m in report.metrics:
        lines.append(
            f"| `{m['name']}` | {m['mean_ms']:.4f} | {m['median_ms']:.4f} | "
            f"{m['p95_ms']:.4f} | {m['min_ms']:.4f} | {m['max_ms']:.4f} | {m['stdev_ms']:.4f} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="M2 Avatar Skeleton benchmarks")
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "benchmarks" / "results",
    )
    args = parser.parse_args(argv)
    report = run_suite(iterations=args.iterations, warmup=args.warmup)
    export_report(report, args.out)
    print(f"Wrote M2 benchmarks to {args.out}")
    for m in report.metrics:
        print(f"  {m['name']}: mean={m['mean_ms']:.4f} ms  p95={m['p95_ms']:.4f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
