from motion_engine.rendering.runtime import RuntimeFactory, PlaybackMode


def test_retarget_pipeline():
    rt = RuntimeFactory().debug()
    rt.startup()
    rt.select_avatar("fixture")
    rt.set_playback_mode(PlaybackMode.RETARGET)
    rt.select_mapping("test_two_bone")
    frames = rt.run_frames(10)
    assert len(frames) == 10
    assert frames[0].metadata.get("mode") == "retarget"
    rt.shutdown()
