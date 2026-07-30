from motion_engine.rendering.runtime.runtime_cache import RuntimeCache


def test_runtime_cache():
    c = RuntimeCache()
    c.put("meshes", "m1", object())
    assert c.get("meshes", "m1") is not None
    assert c.hits >= 1
