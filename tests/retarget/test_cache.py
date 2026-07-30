from __future__ import annotations

from motion_engine.rendering.avatar.retarget.cache import RetargetCache
from motion_engine.rendering.avatar.retarget.mapping_factory import MappingFactory


def test_cache_hits():
    c = RetargetCache()
    p = MappingFactory().builtin("test_two_bone")
    assert c.get_profile(p.name) is None
    c.put_profile(p)
    assert c.get_profile(p.name) is p
    assert c.hits >= 1
    c.clear()
    assert c.stats()["profiles"] == 0
