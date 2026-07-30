from motion_engine.rendering.runtime import RuntimeFactory


def test_motion_to_avatar():
    rt = RuntimeFactory().debug()
    frames = rt.one_click(frames=5).frames
    assert frames == 5
