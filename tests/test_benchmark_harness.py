"""Benchmark harness smoke tests."""

from __future__ import annotations

from benchmarks.harness import BenchmarkReport, run_suite


def test_benchmark_suite_runs() -> None:
    report = run_suite(repeats=2)
    assert isinstance(report, BenchmarkReport)
    assert len(report.results) >= 5
    names = {r.name for r in report.results}
    assert "avatar_load" in names
    assert "scene_graph_create" in names
    data = report.to_dict()
    assert "benchmarks" in data
    assert all(r.mean_ms >= 0 for r in report.results)
