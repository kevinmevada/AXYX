"""High-resolution timing utilities for research-grade benchmarks.

Uses ``time.perf_counter_ns()`` exclusively. Never use ``time.time()``.
"""

from __future__ import annotations

import statistics
import time
import tracemalloc
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator, Sequence


def ns_to_ms(ns: int) -> float:
    """Convert nanoseconds to milliseconds."""
    return ns / 1_000_000.0


def ns_to_us(ns: int) -> float:
    """Convert nanoseconds to microseconds."""
    return ns / 1_000.0


@dataclass(slots=True)
class TimingStats:
    """Aggregate statistics for a named metric (milliseconds)."""

    name: str
    samples_ms: list[float] = field(default_factory=list)
    memory_peak_kib: float = 0.0
    extras: dict[str, Any] = field(default_factory=dict)

    @property
    def n(self) -> int:
        return len(self.samples_ms)

    @property
    def min_ms(self) -> float:
        return min(self.samples_ms) if self.samples_ms else 0.0

    @property
    def max_ms(self) -> float:
        return max(self.samples_ms) if self.samples_ms else 0.0

    @property
    def mean_ms(self) -> float:
        return statistics.fmean(self.samples_ms) if self.samples_ms else 0.0

    @property
    def median_ms(self) -> float:
        return float(statistics.median(self.samples_ms)) if self.samples_ms else 0.0

    @property
    def stdev_ms(self) -> float:
        if len(self.samples_ms) < 2:
            return 0.0
        return float(statistics.stdev(self.samples_ms))

    @property
    def p95_ms(self) -> float:
        if not self.samples_ms:
            return 0.0
        ordered = sorted(self.samples_ms)
        idx = min(len(ordered) - 1, max(0, int(round(0.95 * (len(ordered) - 1)))))
        return ordered[idx]

    def format_mean(self) -> str:
        """Human-readable mean with adaptive precision."""
        v = self.mean_ms
        if v < 0.01:
            return f"{v * 1000.0:.2f} us"
        if v < 1.0:
            return f"{v:.3f} ms"
        if v < 100.0:
            return f"{v:.2f} ms"
        return f"{v:.1f} ms"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "n": self.n,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
            "mean_ms": self.mean_ms,
            "median_ms": self.median_ms,
            "stdev_ms": self.stdev_ms,
            "p95_ms": self.p95_ms,
            "memory_peak_kib": self.memory_peak_kib,
            "extras": self.extras,
        }


@contextmanager
def measure_ns() -> Iterator[list[int]]:
    """Context manager yielding a one-element list filled with elapsed ns."""
    box: list[int] = [0]
    t0 = time.perf_counter_ns()
    try:
        yield box
    finally:
        box[0] = time.perf_counter_ns() - t0


def time_call_ns(fn: Callable[[], Any]) -> tuple[Any, int]:
    """Run ``fn`` once; return ``(result, elapsed_ns)``."""
    t0 = time.perf_counter_ns()
    result = fn()
    return result, time.perf_counter_ns() - t0


def benchmark(
    name: str,
    fn: Callable[[], Any],
    *,
    iterations: int = 100,
    warmup: int = 1,
    track_memory: bool = True,
) -> TimingStats:
    """Repeat ``fn``, discard warmups, return timing statistics in milliseconds.

    Args:
        name: Metric name.
        fn: Callable under test (should be side-effect free where possible).
        iterations: Number of timed iterations kept.
        warmup: Discarded iterations before measurement (JIT / cache warm).
        track_memory: If True, record peak tracemalloc during the run.
    """
    for _ in range(max(0, warmup)):
        fn()

    samples_ms: list[float] = []
    peak_kib = 0.0
    if track_memory:
        tracemalloc.start()
    try:
        for _ in range(max(1, iterations)):
            _, elapsed_ns = time_call_ns(fn)
            samples_ms.append(ns_to_ms(elapsed_ns))
            if track_memory:
                _, peak = tracemalloc.get_traced_memory()
                peak_kib = max(peak_kib, peak / 1024.0)
    finally:
        if track_memory:
            tracemalloc.stop()

    return TimingStats(name=name, samples_ms=samples_ms, memory_peak_kib=peak_kib)


def percentile(samples: Sequence[float], p: float) -> float:
    """Linear percentile helper (``p`` in 0..100)."""
    if not samples:
        return 0.0
    ordered = sorted(samples)
    if len(ordered) == 1:
        return ordered[0]
    rank = (p / 100.0) * (len(ordered) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(ordered) - 1)
    frac = rank - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


__all__ = [
    "TimingStats",
    "ns_to_ms",
    "ns_to_us",
    "measure_ns",
    "time_call_ns",
    "benchmark",
    "percentile",
]
