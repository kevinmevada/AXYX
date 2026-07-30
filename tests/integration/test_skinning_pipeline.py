from motion_engine.rendering.runtime import RuntimeFactory, PlaybackMode


def test_skinning_pipeline():
    rt = RuntimeFactory().debug()
    rt.startup()
    rt.select_avatar("fixture")
    rt.set_playback_mode(PlaybackMode.BIND)
    fr = rt.prepare() and rt.seek(0)
    assert fr.finite and fr.vertex_count > 0
    rt.shutdown()
