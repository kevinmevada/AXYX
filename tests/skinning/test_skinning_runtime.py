"""SkinningRuntime integration tests."""

from __future__ import annotations

import numpy as np
import pytest

from motion_engine.rendering.avatar.skinning import (
    SkinningAlgorithm,
    SkinningNotSupportedError,
    SkinningRuntime,
)
from tests.skinning.helpers import make_bind, make_mesh_skin, make_segment_mesh, rotate_forearm


def test_bind_pose_no_deformation(mesh, skin, bind) -> None:
    rt = SkinningRuntime()
    out = rt.deform(mesh, skin, bind_pose=bind)
    assert np.allclose(out.positions, mesh.positions, atol=1e-4)
    assert out.indices.shape == mesh.indices.shape
    assert np.allclose(out.uvs, mesh.uvs)


def test_source_mesh_immutable(mesh, skin, bind) -> None:
    before = mesh.positions.copy()
    SkinningRuntime().deform(mesh, skin, bind_pose=bind)
    assert np.allclose(mesh.positions, before)


def test_bent_forearm_moves_tip(mesh, skin, bind) -> None:
    anim = rotate_forearm(bind, 90.0)
    out = SkinningRuntime().deform(mesh, skin, pose=anim)
    # tip (x=1) fully on forearm should leave the X axis
    tip = out.positions[-1]
    assert abs(float(tip[1])) > 0.1 or abs(float(tip[0]) - 1.0) > 0.1


def test_dqs_not_supported(mesh, skin, bind) -> None:
    rt = SkinningRuntime(algorithm=SkinningAlgorithm.DUAL_QUATERNION)
    with pytest.raises(SkinningNotSupportedError):
        rt.deform(mesh, skin, bind_pose=bind)
