"""Mesh deformer tests."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.skinning import MeshDeformer, SkinningResult


def test_preserves_topology(mesh) -> None:
    res = SkinningResult(positions=mesh.positions * 2, normals=mesh.normals)
    out = MeshDeformer().deform(mesh, res)
    assert np.array_equal(out.indices, mesh.indices)
    assert np.allclose(out.uvs, mesh.uvs)
    assert out.vertex_count == mesh.vertex_count
