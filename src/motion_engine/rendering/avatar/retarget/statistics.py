"""Retarget statistics aggregation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

import numpy as np

from motion_engine.rendering.avatar.retarget.types import RetargetStatistics


@dataclass
class StatisticsAggregator:
    """Collect per-frame stats into summary."""

    samples: list[RetargetStatistics] = field(default_factory=list)

    def add(self, stats: RetargetStatistics) -> None:
        self.samples.append(stats)

    def summary(self) -> dict[str, Any]:
        if not self.samples:
            return {"count": 0}
        times = np.asarray([s.retarget_time_ns for s in self.samples], dtype=np.float64)
        coverages = np.asarray([s.coverage for s in self.samples], dtype=np.float64)
        violations = int(sum(s.constraint_violations for s in self.samples))
        return {
            "count": len(self.samples),
            "mapped_bones_mean": float(np.mean([s.mapped_bones for s in self.samples])),
            "coverage_mean": float(np.mean(coverages)),
            "coverage_min": float(np.min(coverages)),
            "scale_ratio": float(self.samples[-1].scale_ratio),
            "constraint_violations_total": violations,
            "retarget_time_ns": _timing(times),
        }


def _timing(arr: np.ndarray) -> dict[str, float]:
    if arr.size == 0:
        return {}
    return {
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "stdev": float(np.std(arr)),
        "p95": float(np.percentile(arr, 95)),
    }


def merge_stats(items: Sequence[RetargetStatistics]) -> RetargetStatistics:
    if not items:
        return RetargetStatistics()
    last = items[-1]
    return RetargetStatistics(
        mapped_bones=last.mapped_bones,
        ignored_source=last.ignored_source,
        ignored_target=last.ignored_target,
        missing_source=last.missing_source,
        missing_target=last.missing_target,
        scale_ratio=last.scale_ratio,
        constraint_violations=sum(s.constraint_violations for s in items),
        coverage=float(np.mean([s.coverage for s in items])),
        frame_time_ns=int(np.mean([s.frame_time_ns for s in items])),
        retarget_time_ns=int(np.mean([s.retarget_time_ns for s in items])),
        extra={"frames": len(items)},
    )


__all__ = ["StatisticsAggregator", "merge_stats"]
