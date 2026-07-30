from __future__ import annotations

from motion_engine.rendering.avatar.retarget.translation_mapper import TranslationMapper
from motion_engine.rendering.avatar.retarget.coordinate_mapper import CoordinateMapper
from motion_engine.rendering.avatar.retarget.types import AXYX_COORDS


def test_uniform_scale():
    tm = TranslationMapper(uniform_scale=2.0)
    assert tm.map((1, 2, 3)) == (2.0, 4.0, 6.0)


def test_relative():
    tm = TranslationMapper()
    assert tm.relative((3, 4, 5), (1, 1, 1)) == (2.0, 3.0, 4.0)


def test_with_coords():
    tm = TranslationMapper(CoordinateMapper(AXYX_COORDS, AXYX_COORDS), uniform_scale=1.0)
    assert tm.map((1, 0, 0)) == (1.0, 0.0, 0.0)
