"""Visual / workflow checks for Phase 1 system demos."""

from __future__ import annotations

from motion_engine.rendering.runtime import RuntimeFactory, PlaybackMode
from motion_engine.rendering.runtime.runtime_configuration import get_preset


def test_visual_idle_walk_run_modes():
    rt = RuntimeFactory().debug()
    rt.startup()
    rt.select_avatar("fixture")
    rt.set_playback_mode(PlaybackMode.ANIMATION)
    rt.prepare()
    # switch clips if available
    clips = rt.context.extras.get("anim_clips") if rt.context else None
    assert clips is not None
    for name in ("idle", "walk", "run", "jump"):
        if name in clips:
            player = rt.context.extras["anim_player"]
            player.load(clips[name])
            fr = rt.seek(0)
            assert fr.finite
    rt.shutdown()


def test_visual_retarget_mirror_root():
    cfg = get_preset("debug")
    cfg.mirror = True
    cfg.root_motion = "in_place"
    from motion_engine.rendering.runtime import DigitalTwinRuntime

    rt = DigitalTwinRuntime(cfg)
    rt.startup()
    rt.select_avatar("fixture")
    rt.select_mapping("test_two_bone")
    frames = rt.run_frames(8)
    assert all(f.finite for f in frames)
    rt.shutdown()


def test_visual_avatar_switching():
    rt = RuntimeFactory().debug()
    rt.startup()
    for avatar in ("fixture", "army_girl", "metahuman"):
        rt.select_avatar(avatar)
        rt.prepare()
        # If assets missing, loader falls back to fixture — force compatible mapping
        if "fixture" in rt.session.avatar_name:
            rt.select_mapping("test_two_bone")
            rt.prepare()
        fr = rt.seek(0)
        assert fr.finite
    rt.shutdown()
