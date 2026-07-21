"""M4 visual validation — bind / single-bone / automated sweeps."""

from __future__ import annotations

import numpy as np
import pytest

from motion_engine.rendering.avatar.skinning.debug import (
    reset_to_bind,
    rotate_bone,
    sweep_all_bones,
    sweep_bone,
    validate_deformed_mesh,
    weight_heatmap_scalars,
)
from motion_engine.rendering.avatar.skinning import SkinningRuntime
from motion_engine.rendering.avatar.skinning.debug.session import SkinningDebugSession


@pytest.fixture
def session() -> SkinningDebugSession:
    return SkinningDebugSession.load_segment_fixture()


def test_bind_pose_matches_rest(session: SkinningDebugSession) -> None:
    out = session.reset()
    assert np.allclose(out.positions, session.mesh.positions, atol=1e-4)
    report = validate_deformed_mesh(session.mesh, out)
    assert report.ok


def test_rotate_one_bone_moves_tip(session: SkinningDebugSession) -> None:
    out = session.set_bone_euler("forearm", x=0, y=0, z=90)
    assert not np.allclose(out.positions[-1], session.mesh.positions[-1], atol=1e-3)
    assert validate_deformed_mesh(session.mesh, out).ok


def test_heatmap_selected_bone(session: SkinningDebugSession) -> None:
    bi = session.skeleton.index_of("forearm")
    s = weight_heatmap_scalars(session.skin, bi)
    assert s.shape[0] == session.mesh.vertex_count
    assert float(s[-1]) > 0.9  # tip on forearm


def test_stress_angles_finite(session: SkinningDebugSession) -> None:
    rt = SkinningRuntime()
    for angle in (0, 45, 90, 135, 180):
        pose = rotate_bone(reset_to_bind(session.bind), "forearm", axis="z", angle=angle)
        out = rt.deform(session.mesh, session.skin, bind_pose=session.bind, pose=pose)
        assert validate_deformed_mesh(session.mesh, out).ok


def test_automated_bone_sweep(session: SkinningDebugSession) -> None:
    reports = sweep_all_bones(
        mesh=session.mesh,
        skin=session.skin,
        bind=session.bind,
        angles=[-45, 0, 45, 90],
        axis="z",
    )
    assert reports
    assert all(r.ok for r in reports)


def test_rotate_helper_independent(session: SkinningDebugSession) -> None:
    a = reset_to_bind(session.bind)
    b = rotate_bone(a, "forearm", axis="z", angle=30)
    assert a.bones[1] is not b.bones[1]
    assert not np.allclose(a.bones[1].global_matrix, b.bones[1].global_matrix)


@pytest.mark.skipif(
    not __import__("pathlib").Path("assets/avatars/metahuman/cache/body_lod3.npz").exists(),
    reason="MetaHuman assets not present",
)
def test_metahuman_bind_and_arm_sweep() -> None:
    session = SkinningDebugSession.load_metahuman(lod=3)
    out = session.reset()
    assert validate_deformed_mesh(session.mesh, out).ok
    # Prefer Unreal-style name
    bone = "upperarm_l" if session.skeleton.exists("upperarm_l") else session.bone_names[1]
    report = sweep_bone(
        mesh=session.mesh,
        skin=session.skin,
        bind=session.bind,
        bone_name=bone,
        angles=[-30, 0, 30, 60],
        axis="z",
    )
    assert report.ok, report.failures
