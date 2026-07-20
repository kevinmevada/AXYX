"""Tests for the rendering architecture package (Phase-0)."""

from __future__ import annotations

from motion_engine.bone_geometry import transform_bone, profile_for_bone
from motion_engine.rendering import (
    AvatarManager,
    MaterialLibrary,
    ProceduralAvatar,
    RenderGraph,
    StudioEnvironment,
)
from motion_engine.rendering.avatar.procedural import ProceduralPoseFrame
from motion_engine.rendering.rendergraph import DEFAULT_PASS_ORDER


def test_procedural_avatar_roundtrip() -> None:
    avatar = ProceduralAvatar()
    avatar.load()
    assert avatar.is_loaded
    frame = ProceduralPoseFrame()
    avatar.update(frame)
    assert avatar.frame is frame


def test_avatar_manager_active_switch() -> None:
    mgr = AvatarManager()
    a = ProceduralAvatar("procedural")
    b = ProceduralAvatar("procedural_b")
    mgr.register(a, make_active=True)
    mgr.register(b)
    assert mgr.active_name == "procedural"
    mgr.set_active("procedural_b")
    assert mgr.get_active() is b


def test_render_graph_default_order() -> None:
    graph = RenderGraph.create_default()
    names = [p.name for p in graph._passes]
    assert names == list(DEFAULT_PASS_ORDER)


def test_material_library_presets() -> None:
    lib = MaterialLibrary()
    assert lib.bone.metallic >= 0.9
    assert lib.joint.metallic >= 0.8
    assert lib.floor.roughness > 0.5


def test_bone_geometry_compat_shim() -> None:
    profile = profile_for_bone("LFemur")
    assert profile.shaft_radius > 0
    import numpy as np

    unit, _ = __import__(
        "motion_engine.bone_geometry", fromlist=["build_unit_bone_template"]
    ).build_unit_bone_template(profile)
    placed = transform_bone(
        unit,
        np.array([0.0, 0.0, 0.0]),
        np.array([0.0, 0.0, 100.0]),
        radial_scale=20.0,
    )
    assert placed.shape[1] == 3


def test_studio_environment_constructs() -> None:
    env = StudioEnvironment()
    assert env._ibl_ready is False
