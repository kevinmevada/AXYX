"""Pipeline stage profiler."""

from __future__ import annotations

import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

import numpy as np

try:
    import psutil  # type: ignore
except ImportError:  # pragma: no cover
    psutil = None


@dataclass
class StageSample:
    name: str
    elapsed_ns: int


@dataclass
class RuntimeProfiler:
    """Collect stage timings + optional memory."""

    enabled: bool = True
    samples: dict[str, list[int]] = field(default_factory=lambda: defaultdict(list))
    frame_samples_ns: list[int] = field(default_factory=list)

    def reset(self) -> None:
        self.samples.clear()
        self.frame_samples_ns.clear()

    @contextmanager
    def measure(self, stage: str) -> Iterator[None]:
        if not self.enabled:
            yield
            return
        t0 = time.perf_counter_ns()
        try:
            yield
        finally:
            self.samples[stage].append(time.perf_counter_ns() - t0)

    def record(self, stage: str, elapsed_ns: int) -> None:
        if self.enabled:
            self.samples[stage].append(int(elapsed_ns))

    def record_frame(self, elapsed_ns: int) -> None:
        if self.enabled:
            self.frame_samples_ns.append(int(elapsed_ns))

    def memory_mb(self) -> float:
        if psutil is None:
            return 0.0
        try:
            proc = psutil.Process()
            return float(proc.memory_info().rss) / (1024.0 * 1024.0)
        except Exception:  # noqa: BLE001
            return 0.0

    def summary(self) -> dict[str, Any]:
        out: dict[str, Any] = {"memory_mb": self.memory_mb()}
        for name, vals in self.samples.items():
            arr = np.asarray(vals, dtype=np.float64)
            out[name] = _timing(arr)
        if self.frame_samples_ns:
            frames = np.asarray(self.frame_samples_ns, dtype=np.float64)
            out["frame"] = _timing(frames)
            mean_s = float(np.mean(frames)) / 1e9
            out["fps_estimate"] = (1.0 / mean_s) if mean_s > 0 else 0.0
        return out


def _timing(arr: np.ndarray) -> dict[str, float]:
    if arr.size == 0:
        return {}
    return {
        "count": float(arr.size),
        "min_ns": float(np.min(arr)),
        "max_ns": float(np.max(arr)),
        "mean_ns": float(np.mean(arr)),
        "median_ns": float(np.median(arr)),
        "stdev_ns": float(np.std(arr)),
        "p95_ns": float(np.percentile(arr, 95)),
        "mean_ms": float(np.mean(arr)) / 1e6,
    }


__all__ = ["StageSample", "RuntimeProfiler"]
