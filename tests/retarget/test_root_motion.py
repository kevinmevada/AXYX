from __future__ import annotations

from motion_engine.rendering.avatar.retarget.root_motion import RootMotionProcessor
from motion_engine.rendering.avatar.retarget.types import RootMotionMode


def test_in_place_locks_origin():
    rm = RootMotionProcessor(RootMotionMode.IN_PLACE)
    a = rm.process_translation((1, 0, 1), frame_index=0)
    b = rm.process_translation((5, 0, 1.1), frame_index=1)
    assert a[0] == 1.0
    assert b[0] == 1.0  # planar locked to origin X


def test_world_passthrough():
    rm = RootMotionProcessor(RootMotionMode.WORLD)
    t = rm.process_translation((2, 3, 4), frame_index=0)
    assert t == (2.0, 3.0, 4.0)


def test_loop_correction():
    rm = RootMotionProcessor(RootMotionMode.WORLD)
    delta = rm.loop_correction([(0, 0, 0), (1, 0, 0), (2, 0, 0)])
    assert abs(delta[0] - 2.0) < 1e-9
