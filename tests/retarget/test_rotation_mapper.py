from __future__ import annotations

import math

import numpy as np

from motion_engine.rendering.avatar.retarget._quat import q_axis_angle, q_normalize
from motion_engine.rendering.avatar.retarget.rotation_mapper import RotationMapper


def test_map_local_preserves_unit():
    rm = RotationMapper()
    q = q_axis_angle((0, 1, 0), math.radians(45))
    out = rm.map_local(q)
    assert abs(np.linalg.norm(out) - 1.0) < 1e-9


def test_relative_bind_roundtrip():
    rm = RotationMapper()
    bind = q_normalize((0, 0, 0, 1))
    anim = q_axis_angle((1, 0, 0), 0.3)
    delta = rm.relative_to_bind(anim, bind)
    back = rm.apply_delta(bind, delta)
    assert np.allclose(back, anim, atol=1e-9)
