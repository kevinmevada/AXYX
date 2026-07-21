"""CPU skinner tests."""

from __future__ import annotations

import numpy as np
import pytest

from motion_engine.rendering.avatar.skinning import CpuSkinner, build_matrix_palette
from motion_engine.rendering.avatar.skinning.vertex_transform import transform_point


def test_cpu_skinner_bind(mesh, skin, bind) -> None:
    pal = build_matrix_palette(bind)
    res = CpuSkinner().skin(mesh, skin.weight_table, pal)
    assert np.allclose(res.positions, mesh.positions, atol=1e-4)


def test_transform_point() -> None:
    m = np.eye(4)
    m[0, 3] = 2
    assert transform_point(m, [1, 0, 0])[0] == pytest.approx(3.0)
