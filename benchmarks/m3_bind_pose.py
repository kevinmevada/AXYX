#!/usr/bin/env python3
"""AXYX Phase 1 — Milestone 3 Bind Pose benchmarks.

Run::

    python -m benchmarks.m3_bind_pose --iterations 100
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
from motion_engine.rendering.avatar.pose import (  # noqa: E402
    BindPoseFactory,
    export_json,
    validate_pose,
)
from motion_engine.rendering.avatar.pose.matrix_utils import invert_affine  # noqa: E402
from tests.pose.helpers import make_chain_skeleton  # noqa: E402


@dataclass
class M3BenchmarkReport:
    created_utc: str
    iterations: int
    environment: dict[str, Any]
    metrics: list[dict[str, Any]] = field(default_factory=list)

    def add(self, stats: TimingStats) -> None:
        self.metrics.append(stats.to_dict())


def run_suite(iterations: int = 100, warmup: int = 2) -> M3BenchmarkReport:
    report = M3BenchmarkReport(
        created_utc=datetime.now(timezone.utc).isoformat(),
        iterations=iterations,
        environment={
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
    )
    skeleton = make_chain_skeleton(128)
    factory = BindPoseFactory()
    pose = factory.from_skeleton(skeleton)

    report.add(
        benchmark(
            "pose_construction",
            lambda: factory.from_skeleton(skeleton),
            iterations=iterations,
            warmup=warmup,
        )
    )
    report.add(
        benchmark(
            "transform_propagation",
            lambda: BindPoseFactory(recompute_world_from_local=True).from_skeleton(skeleton),
            iterations=iterations,
            warmup=warmup,
        )
    )
    report.add(
        benchmark(
            "matrix_inversion",
            lambda: [invert_affine(b.rest_matrix) for b in pose],
            iterations=iterations,
            warmup=warmup,
        )
    )
    report.add(
        benchmark(
            "validation",
            lambda: validate_pose(pose),
            iterations=iterations,
            warmup=warmup,
        )
    )
    report.add(
        benchmark(
            "lookup",
            lambda: pose.find("b64"),
            iterations=iterations,
            warmup=warmup,
        )
    )
    report.add(
        benchmark(
            "serialization",
            lambda: export_json(pose),
            iterations=max(10, iterations // 5),
            warmup=warmup,
        )
    )
    return report


def export_report(report: M3BenchmarkReport, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "m3_bind_pose.json").write_text(
        json.dumps(asdict(report), indent=2), encoding="utf-8"
    )
    with (out_dir / "m3_bind_pose.csv").open("w", newline="", encoding="utf-8") as fh:
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
        "# M3 Bind Pose Benchmarks",
        "",
        f"- Created: `{report.created_utc}`",
        f"- Iterations: `{report.iterations}`",
        "",
        "| Metric | Mean | Median | P95 | Min | Max | Stdev |",
        "|--------|------|--------|-----|-----|-----|-------|",
    ]
    for m in report.metrics:
        lines.append(
            f"| `{m['name']}` | {m['mean_ms']:.4f} | {m['median_ms']:.4f} | "
            f"{m['p95_ms']:.4f} | {m['min_ms']:.4f} | {m['max_ms']:.4f} | {m['stdev_ms']:.4f} |"
        )
    (out_dir / "m3_bind_pose.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="M3 Bind Pose benchmarks")
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "benchmarks" / "results")
    args = parser.parse_args(argv)
    report = run_suite(iterations=args.iterations, warmup=args.warmup)
    export_report(report, args.out)
    print(f"Wrote M3 benchmarks to {args.out}")
    for m in report.metrics:
        print(f"  {m['name']}: mean={m['mean_ms']:.4f} ms  p95={m['p95_ms']:.4f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
