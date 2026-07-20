"""Tests for research-grade M1 benchmark utilities."""

from __future__ import annotations

import time

from benchmarks.timing import TimingStats, benchmark, ns_to_ms, time_call_ns


def test_perf_counter_ns_path() -> None:
    def _work() -> int:
        return sum(range(1000))

    result, elapsed_ns = time_call_ns(_work)
    assert result == sum(range(1000))
    assert elapsed_ns >= 0
    assert ns_to_ms(elapsed_ns) >= 0.0


def test_benchmark_statistics() -> None:
    stats = benchmark("nop", lambda: None, iterations=10, warmup=1, track_memory=False)
    assert isinstance(stats, TimingStats)
    assert stats.n == 10
    assert stats.min_ms <= stats.median_ms <= stats.max_ms
    assert stats.p95_ms >= stats.min_ms
    d = stats.to_dict()
    assert "stdev_ms" in d and "p95_ms" in d


def test_m1_suite_smoke() -> None:
    from benchmarks.m1_asset_pipeline import format_table, run_m1_benchmarks

    report = run_m1_benchmarks(iterations=3, warmup=0, lod=3)
    assert report.metric("cold_avatar_load") is not None
    assert report.metric("warm_avatar_load") is not None
    assert report.metric("mesh_load_total") is not None
    table = format_table(report)
    assert "Cold Avatar Load" in table
    assert "Warm Avatar Load" in table
    assert "ms" in table.lower() or "us" in table.lower()
