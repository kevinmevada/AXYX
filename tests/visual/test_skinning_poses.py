"""Visual / geometric skinning checks (no GUI — analytical poses)."""

from __future__ import annotations

import numpy as np
import pytest

from motion_engine.rendering.avatar.skinning import SkinningRuntime
from tests.skinning.helpers import make_bind, make_mesh_skin, make_segment_mesh, rotate_forearm


def _finite(mesh_out) -> None:
    assert np.all(np.isfinite(mesh_out.positions))
    assert np.all(np.isfinite(mesh_out.normals))


def _topology_ok(src, out) -> None:
    assert np.array_equal(out.indices, src.indices)
    assert out.vertex_count == src.vertex_count


def test_visual_bind_pose() -> None:
    mesh, bind = make_segment_mesh(8), make_bind()
    skin = make_mesh_skin(mesh)
    out = SkinningRuntime().deform(mesh, skin, bind_pose=bind)
    _finite(out)
    _topology_ok(mesh, out)
    assert np.allclose(out.positions, mesh.positions, atol=1e-4)


def test_visual_raised_arm() -> None:
    mesh, bind = make_segment_mesh(8), make_bind()
    skin = make_mesh_skin(mesh)
    anim = rotate_forearm(bind, 45.0)
    out = SkinningRuntime().deform(mesh, skin, pose=anim)
    _finite(out)
    _topology_ok(mesh, out)
    # not exploded
    assert float(np.max(np.linalg.norm(out.positions, axis=1))) < 10.0


def test_visual_bent_elbow() -> None:
    mesh, bind = make_segment_mesh(8), make_bind()
    skin = make_mesh_skin(mesh)
    anim = rotate_forearm(bind, 90.0)
    out = SkinningRuntime().deform(mesh, skin, pose=anim)
    _finite(out)
    # tip moved
    assert not np.allclose(out.positions[-1], mesh.positions[-1], atol=1e-3)


def test_visual_rotated_spine_proxy() -> None:
    """Proxy: rotate root (whole chain) — no detach."""
    mesh, bind = make_segment_mesh(6), make_bind()
    skin = make_mesh_skin(mesh)
    anim = rotate_forearm(bind, 0.0)
    # rotate root local
    from motion_engine.rendering.avatar.pose.pose import BonePose, AnimationPose
    from motion_engine.rendering.avatar.pose.transform_propagation import (
        propagate_world_transforms,
    )

    locals_m = [b.local_matrix.copy() for b in anim.bones]
    rot = np.eye(4)
    a = np.deg2rad(30)
    rot[0, 0] = np.cos(a)
    rot[0, 1] = -np.sin(a)
    rot[1, 0] = np.sin(a)
    rot[1, 1] = np.cos(a)
    locals_m[0] = rot @ locals_m[0]
    worlds = list(
        propagate_world_transforms(locals_m, [b.parent_index for b in anim.bones]).world_matrices
    )
    bones = [
        BonePose.from_matrices(
            bone_id=b.bone_id,
            index=b.index,
            name=b.name,
            parent_index=b.parent_index,
            children=b.children,
            local_matrix=locals_m[i],
            global_matrix=worlds[i],
            rest_matrix=b.rest_matrix,
            inverse_bind_matrix=b.inverse_bind_matrix,
        )
        for i, b in enumerate(anim.bones)
    ]
    posed = AnimationPose(_name="spine", _bones=bones)
    out = SkinningRuntime().deform(mesh, skin, pose=posed)
    _finite(out)
    _topology_ok(mesh, out)


def test_visual_walking_proxy_oscillation() -> None:
    mesh, bind = make_segment_mesh(8), make_bind()
    skin = make_mesh_skin(mesh)
    for deg in (-20, 0, 20, 40):
        out = SkinningRuntime().deform(mesh, skin, pose=rotate_forearm(bind, float(deg)))
        _finite(out)
        assert float(np.linalg.norm(out.positions[-1] - out.positions[0])) < 5.0
