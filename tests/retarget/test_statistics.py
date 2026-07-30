from __future__ import annotations

from motion_engine.rendering.avatar.retarget.statistics import StatisticsAggregator, merge_stats
from motion_engine.rendering.avatar.retarget.types import RetargetStatistics


def test_aggregator_summary():
    agg = StatisticsAggregator()
    for i in range(5):
        agg.add(
            RetargetStatistics(
                mapped_bones=2,
                coverage=0.9,
                retarget_time_ns=1000 + i,
                scale_ratio=1.1,
            )
        )
    s = agg.summary()
    assert s["count"] == 5
    assert "retarget_time_ns" in s
    assert "mean" in s["retarget_time_ns"]


def test_merge_stats():
    items = [RetargetStatistics(mapped_bones=1, coverage=0.5, constraint_violations=1) for _ in range(3)]
    m = merge_stats(items)
    assert m.constraint_violations == 3
