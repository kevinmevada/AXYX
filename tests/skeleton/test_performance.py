"""Lightweight performance sanity checks for M2 skeleton."""

from __future__ import annotations

import time

from motion_engine.rendering.avatar.skeleton import AvatarSkeletonFactory
from tests.skeleton.helpers import make_chain_imported


def test_lookup_is_fast() -> None:
    sk = AvatarSkeletonFactory().from_imported(make_chain_imported(200))
    t0 = time.perf_counter_ns()
    for _ in range(10_000):
        _ = sk.find("b50")
    elapsed_ms = (time.perf_counter_ns() - t0) / 1e6
    # Extremely loose bound — guards against accidental O(n) scans.
    assert elapsed_ms < 500.0


def test_validation_linear() -> None:
    sk = AvatarSkeletonFactory().from_imported(make_chain_imported(300))
    t0 = time.perf_counter_ns()
    report = sk.validate()
    elapsed_ms = (time.perf_counter_ns() - t0) / 1e6
    assert report.ok
    assert elapsed_ms < 200.0


def test_traversal_visits_all() -> None:
    sk = AvatarSkeletonFactory().from_imported(make_chain_imported(100))
    assert len(list(sk.traversal.dfs())) == 100
    assert len(list(sk.traversal.bfs())) == 100
