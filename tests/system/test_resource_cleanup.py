from motion_engine.rendering.runtime import RuntimeFactory


def test_cleanup_clears_cache_and_context():
    rt = RuntimeFactory().debug()
    rt.startup()
    rt.select_avatar("fixture")
    rt.prepare()
    assert rt.manager.cache.stats()["avatars"] >= 1
    rt.shutdown()
    assert rt.context is None
    assert rt.manager.cache.stats()["avatars"] == 0
