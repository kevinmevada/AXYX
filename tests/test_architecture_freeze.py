"""Architecture freeze / public API / state machine / asset ID tests."""

from __future__ import annotations

import pytest

from motion_engine.api import API_VERSION
from motion_engine.api import avatar as avatar_api
from motion_engine.api import rendering as rendering_api
from motion_engine.api import scene as scene_api
from motion_engine.api import viewer as viewer_api
from motion_engine.rendering.assets.asset_ids import (
    list_asset_ids,
    preset_key_from_id,
    resolve_avatar_manifest,
    resolve_asset_id,
)
from motion_engine.rendering.backend import (
    NULL_CAPABILITIES,
    PYVISTA_CAPABILITIES,
)
from motion_engine.rendering.errors import (
    AvatarLoadError,
    RenderErrorCode,
    ResourceNotFoundError,
)
from motion_engine.rendering.interfaces import (
    Avatar,
    BackendCapabilities,
    Material,
    RenderPass,
    SceneNode,
)
from motion_engine.rendering.materials import MaterialLibrary, PBRMaterial
from motion_engine.rendering.metrics import PerformanceMetrics
from motion_engine.rendering.serialization import SceneSerializer, SettingsSerializer
from motion_engine.rendering.state import RendererState, RendererStateMachine
from motion_engine.renderer import NullRenderer


def test_api_version() -> None:
    assert API_VERSION.startswith("1.")


def test_api_modules_export_core_symbols() -> None:
    assert rendering_api.PyVistaRenderer is not None
    assert rendering_api.SceneGraph is not None
    assert avatar_api.AvatarManager is not None
    assert avatar_api.ProceduralAvatar is not None
    assert viewer_api.SkeletonViewer is not None
    assert scene_api.MaterialLibrary is not None
    assert scene_api.LightingManager is not None


def test_interfaces_are_importable() -> None:
    assert issubclass(Avatar, object)
    assert issubclass(RenderPass, object)
    assert issubclass(SceneNode, object)
    caps = BackendCapabilities(name="test")
    assert caps.supports_pbr is True
    lib = MaterialLibrary()
    mat: Material = lib.get("graphite")
    assert mat.metallic > 0


def test_renderer_state_machine() -> None:
    sm = RendererStateMachine()
    assert sm.state is RendererState.UNINITIALIZED
    assert sm.transition(RendererState.INITIALIZING)
    assert sm.transition(RendererState.READY)
    assert sm.transition(RendererState.RENDERING)
    assert sm.transition(RendererState.READY)
    assert not sm.transition(RendererState.UNINITIALIZED)
    assert sm.transition(RendererState.SHUTTING_DOWN)
    assert sm.transition(RendererState.DESTROYED)


def test_null_renderer_state_and_capabilities() -> None:
    r = NullRenderer()
    assert r.capabilities is NULL_CAPABILITIES
    assert r.state_machine.state is RendererState.UNINITIALIZED
    r.initialize()
    assert r.state_machine.state is RendererState.READY
    r.close()
    assert r.state_machine.state is RendererState.DESTROYED


def test_pyvista_capabilities() -> None:
    assert PYVISTA_CAPABILITIES.supports_pbr
    assert PYVISTA_CAPABILITIES.supports_hdri
    assert not PYVISTA_CAPABILITIES.supports_skinning


def test_asset_ids() -> None:
    path = resolve_avatar_manifest("avatar.procedural.default")
    assert path is not None and path.is_file()
    assert resolve_asset_id("material.graphite") is not None
    assert preset_key_from_id("lighting.clinical") == "clinical"
    assert "avatar.procedural.default" in list_asset_ids(prefix="avatar.")
    assert resolve_asset_id("no.such.id") is None


def test_performance_metrics_always_present() -> None:
    m = PerformanceMetrics()
    d = m.to_dict()
    for key in (
        "frame_ms",
        "update_ms",
        "animation_ms",
        "skinning_ms",
        "render_ms",
        "fps",
        "triangles",
        "draw_calls",
        "gpu_upload_bytes",
        "memory_bytes",
    ):
        assert key in d
    m.apply_frame_time(0.016)
    assert m.fps > 0
    m.reset_counters()
    assert m.draw_calls == 0


def test_render_error_codes() -> None:
    err = AvatarLoadError("failed")
    assert err.code is RenderErrorCode.AVATAR_LOAD
    missing = ResourceNotFoundError("gone")
    assert missing.code is RenderErrorCode.RESOURCE_NOT_FOUND


def test_serialization_stubs_reserved() -> None:
    with pytest.raises(NotImplementedError):
        SceneSerializer().dumps(None)
    with pytest.raises(NotImplementedError):
        SettingsSerializer().loads({})


def test_pbr_material_is_material_protocol() -> None:
    mat = PBRMaterial("x", (1.0, 1.0, 1.0), 0.5, 0.5)
    assert isinstance(mat, PBRMaterial)
