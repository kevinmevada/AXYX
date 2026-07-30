from motion_engine.rendering.runtime.runtime_profiler import RuntimeProfiler


def test_profiler_summary():
    p = RuntimeProfiler()
    with p.measure("skinning"):
        _ = [i * i for i in range(100)]
    p.record_frame(12345)
    s = p.summary()
    assert "skinning" in s
    assert "frame" in s
