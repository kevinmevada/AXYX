from __future__ import annotations

from motion_engine.rendering.avatar.retarget.filters import (
    FilterConfig,
    MovingAverageFilter,
    TemporalFilter,
    moving_average,
)
from motion_engine.rendering.avatar.retarget.types import FilterKind


def test_moving_average_scalar():
    out = moving_average([1, 2, 3, 4], window=2)
    assert out[0] == 1
    assert out[1] == 1.5


def test_quat_ma_unit():
    f = MovingAverageFilter(3)
    q = f.push_quat("a", (0, 0, 0, 1))
    assert abs(sum(x * x for x in q) - 1.0) < 1e-9


def test_temporal_filter_kinds():
    for kind in FilterKind:
        tf = TemporalFilter(FilterConfig(kind=kind, window=3))
        q = tf.filter_quat("b", (0, 0, 0, 1))
        assert abs(sum(x * x for x in q) - 1.0) < 1e-6
