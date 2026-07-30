from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.retarget.coordinate_mapper import CoordinateMapper
from motion_engine.rendering.avatar.retarget.types import AXYX_COORDS, Y_UP_RIGHT
from motion_engine.rendering.avatar.retarget._quat import q_identity


def test_identity_coords():
    m = CoordinateMapper(AXYX_COORDS, AXYX_COORDS)
    v = m.map_vector((1.0, 2.0, 3.0))
    assert np.allclose(v, (1.0, 2.0, 3.0), atol=1e-9)
    q = m.map_quat(q_identity())
    assert np.allclose(q, (0, 0, 0, 1), atol=1e-9)


def test_z_up_to_y_up_preserves_length():
    m = CoordinateMapper(AXYX_COORDS, Y_UP_RIGHT)
    v = m.map_vector((0.0, 0.0, 1.0), apply_units=False)
    assert abs(np.linalg.norm(v) - 1.0) < 1e-9
