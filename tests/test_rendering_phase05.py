"""Phase-0.5 rendering architecture subsystem tests."""

from __future__ import annotations

from pathlib import Path

from motion_engine.rendering.avatar.avatar_manager import AvatarManager
from motion_engine.rendering.avatar.avatar_manifest import AvatarManifest
from motion_engine.rendering.avatar.procedural import ProceduralAvatar
from motion_engine.rendering.camera import get_camera_profile
from motion_engine.rendering.context import FrameContext, RenderSettings, RenderingContext
from motion_engine.rendering.environment import EnvironmentManager, get_environment_preset
from motion_engine.rendering.events import LightingChanged, RenderEventBus
from motion_engine.rendering.lifecycle import RenderLifecycle, RenderPhase
from motion_engine.rendering.lighting import LightingManager
from motion_engine.rendering.lighting.presets import get_lighting_preset
from motion_engine.rendering.materials import MaterialLibrary
from motion_engine.rendering.plugins import PluginRegistry
from motion_engine.rendering.quality import get_quality
from motion_engine.rendering.rendergraph import RenderGraph
from motion_engine.rendering.resources import ResourceManager
from motion_engine.rendering.scene import SceneGraph
from motion_engine.rendering.scene.scene_node import RenderNode, TransformNode


def test_resource_manager_caches_and_misses() -> None:
    rm = ResourceManager()
    assert rm.safe_get("mesh", "missing") is None
    created = rm.load("mesh", "unit", factory=lambda: {"verts": 8})
    assert created == {"verts": 8}
    assert rm.load("mesh", "unit", factory=lambda: {"verts": 99}) == {"verts": 8}
    assert rm.safe_get("mesh", "unit") == {"verts": 8}
    # Missing file path never raises
    assert rm.load("texture", "gone", path=Path("does/not/exist.png")) is None


def test_scene_graph_hierarchy() -> None:
    graph = SceneGraph()
    ground = TransformNode(name="ground")
    avatar = RenderNode(name="avatar")
    graph.add(ground)
    graph.add(avatar, parent=ground)
    assert graph.find("avatar") is avatar
    assert list(graph.iter_render_nodes()) == [avatar]
    graph.clear()
    assert graph.find("avatar") is None


def test_material_library_get() -> None:
    lib = MaterialLibrary()
    assert lib.get("titanium").metallic > 0.5
    assert lib.get("graphite").name == "graphite"
    assert lib.get("glass").roughness < 0.2
    assert lib.get("unknown_xyz").name == "graphite"  # graceful fallback
    lib.register("custom", lib.get("ceramic"))
    assert lib.get("custom").name == "ceramic"


def test_environment_manager_presets() -> None:
    mgr = EnvironmentManager("studio")
    assert mgr.active.name == "studio"
    mgr.set_preset("dark_lab")
    assert mgr.preset_name == "dark_lab"
    assert get_environment_preset("nope").name == "studio"


def test_lighting_manager_presets() -> None:
    mgr = LightingManager("studio")
    assert get_lighting_preset("cinematic").name == "cinematic"
    mgr.set_preset("clinical")
    assert mgr.preset_name == "clinical"
    assert get_lighting_preset("missing").name == "studio"


def test_avatar_manager_and_manifest() -> None:
    mgr = AvatarManager()
    mgr.register(ProceduralAvatar(), make_active=True)
    assert mgr.get_active() is not None
    manifest = AvatarManifest.procedural_default()
    assert manifest is not None
    assert manifest.name == "procedural"
    assert "bone" in manifest.materials


def test_render_graph_and_lifecycle() -> None:
    graph = RenderGraph.create_default()
    assert len(list(graph._passes)) >= 4
    life = RenderLifecycle()
    seen: list[str] = []
    life.on(RenderPhase.INITIALIZE, lambda: seen.append("init"))
    life.on(RenderPhase.LOAD_ASSETS, lambda: seen.append("load"))
    life.on(RenderPhase.CREATE_SCENE, lambda: seen.append("scene"))
    life.run_startup()
    assert seen == ["init", "load", "scene"]
    life.shutdown()
    assert life.phase == RenderPhase.SHUTDOWN


def test_camera_profiles() -> None:
    clinical = get_camera_profile("clinical")
    assert clinical.fov_deg > 0
    assert clinical.focal_length_mm == 85.0
    orbit = get_camera_profile("orbit")
    assert orbit.orbit_sensitivity > clinical.orbit_sensitivity
    assert get_camera_profile("nope").name == "clinical"


def test_quality_and_settings() -> None:
    q = get_quality("ultra")
    assert q.msaa >= 2
    assert get_quality("bogus").name == "high"
    settings = RenderSettings.load()
    assert settings.quality in {"low", "medium", "high", "ultra"}
    assert settings.lighting_preset == "studio"


def test_frame_context_and_events() -> None:
    ctx = RenderingContext(
        avatar_manager=AvatarManager(),
        settings=RenderSettings.defaults(),
    )
    frame = ctx.make_frame(delta_time=0.016, viewport_width=1280, viewport_height=720)
    assert isinstance(frame, FrameContext)
    assert frame.viewport_size == (1280, 720)

    bus = RenderEventBus()
    got: list[str] = []
    bus.subscribe("LightingChanged", lambda e: got.append(e.payload["preset"]))
    bus.emit(LightingChanged("presentation"))
    assert got == ["presentation"]


def test_plugin_registry() -> None:
    reg = PluginRegistry()
    reg.register_material("gold", lambda: {"m": 1.0})
    assert reg.create("material", "gold") == {"m": 1.0}
    assert reg.create("material", "missing") is None
    assert reg.names("material") == ["gold"]
