"""PoseCache tests."""

from __future__ import annotations

from motion_engine.rendering.avatar.pose import PoseCache
from tests.pose.helpers import make_bind_pose


def test_cache_put_get() -> None:
    cache = PoseCache()
    pose = make_bind_pose(3)
    cache.put("a", pose)
    assert "a" in cache
    assert cache.get("a") is pose
    assert cache.hits == 1
    assert cache.get("missing") is None
    assert cache.misses == 1


def test_invalidate_clear() -> None:
    cache = PoseCache()
    pose = make_bind_pose(2)
    cache.put("x", pose)
    cache.invalidate("x")
    assert len(cache) == 0
    cache.put("y", pose)
    cache.clear()
    assert cache.size == 0
    assert cache.hits == 0
