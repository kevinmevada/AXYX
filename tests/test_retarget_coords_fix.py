"""Regression: Army Girl retarget must share Z-up with clinical AXYX."""

from __future__ import annotations

from motion_engine.rendering.avatar.retarget.cache import get_global_cache
from motion_engine.rendering.avatar.retarget.constants import PROFILE_MATLAB_ARMY
from motion_engine.rendering.avatar.retarget.factory import RetargetFactory
from motion_engine.rendering.avatar.retarget.types import AXYX_COORDS, UpAxis


def test_army_girl_profile_is_z_up() -> None:
    get_global_cache().clear()
    factory = RetargetFactory()
    profile = factory.profile(PROFILE_MATLAB_ARMY)
    assert profile.source_coords.up is UpAxis.Z
    assert profile.target_coords.up is UpAxis.Z
    assert profile.source_coords.key() == profile.target_coords.key()
    assert profile.source_coords.key() == AXYX_COORDS.key()


def test_army_girl_coordinate_mapper_is_identity() -> None:
    get_global_cache().clear()
    factory = RetargetFactory()
    eng = factory.engine(PROFILE_MATLAB_ARMY)
    r = eng.coords.rotation_matrix
    assert abs(float(r[0, 0]) - 1.0) < 1e-9
    assert abs(float(r[1, 1]) - 1.0) < 1e-9
    assert abs(float(r[2, 2]) - 1.0) < 1e-9
    assert abs(float(r.sum()) - 3.0) < 1e-6


def test_json_profile_preferred_over_stale_cache() -> None:
    cache = get_global_cache()
    cache.clear()
    factory = RetargetFactory()
    p1 = factory.profile(PROFILE_MATLAB_ARMY)
    assert p1.target_coords.up is UpAxis.Z
    # Simulate stale cache entry being replaced after invalidate
    cache.invalidate_profile(PROFILE_MATLAB_ARMY)
    p2 = factory.profile(PROFILE_MATLAB_ARMY)
    assert p2.target_coords.up is UpAxis.Z
    assert p2.source_coords.key() == p2.target_coords.key()
