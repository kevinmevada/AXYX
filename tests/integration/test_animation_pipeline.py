from motion_engine.rendering.runtime import RuntimeFactory, PlaybackMode


def test_animation_pipeline():
    rt = RuntimeFactory().debug()
    rt.startup()
    rt.select_avatar("fixture")
    rt.set_playback_mode(PlaybackMode.ANIMATION)
    assert all(f.finite for f in rt.run_frames(5))
    rt.shutdown()
