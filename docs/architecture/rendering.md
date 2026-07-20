"""Architecture: AXYX Rendering Subsystem (Phase-0 + Phase-0.5)

## Package diagram

```text
motion_engine/
├── renderer.py              # PUBLIC API facade (Renderer, PyVistaRenderer, NullRenderer)
├── viewer.py                # PUBLIC API — Studio / headless viewer (unchanged contract)
├── bone_geometry.py         # COMPAT shim → rendering.avatar.procedural.bone_geometry
├── camera.py                # PUBLIC API — clinical camera controller
├── colors.py / scene.py     # themes + scene toggles
│
└── rendering/               # Layered, backend-agnostic architecture
    ├── context/             # FrameContext, RenderingContext, RenderSettings
    ├── resources/           # ResourceManager + mesh/texture/shader/material caches
    ├── scene/               # SceneGraph + TransformNode / RenderNode
    ├── avatar/              # Avatar ABC, AvatarManager, manifests, ProceduralAvatar
    ├── environment/         # EnvironmentManager + presets (studio/infinity/dark_lab/…)
    ├── lighting/            # LightingManager + presets (studio/clinical/…)
    ├── materials/           # MaterialLibrary + presets (titanium/graphite/…)
    ├── camera/profiles/     # Named FOV/damping/framing profiles
    ├── quality/             # low / medium / high / ultra
    ├── events/              # RenderEventBus (loose coupling)
    ├── lifecycle/           # Initialize → … → Shutdown
    ├── plugins/             # register_effect / avatar / environment / material
    ├── debug/               # profiler, statistics, debug_draw
    ├── effects/             # trails / vignette / fog hooks
    ├── rendergraph/         # ordered passes
    ├── backend/             # RenderBackend protocol (future Unreal/GL/Vulkan)
    └── assets/              # ASSETS_ROOT → repo assets/
```

Config + assets:

```text
config/rendering.yaml          # all rendering defaults (no magic constants)
assets/avatars/<name>/avatar.json   # skeleton, materials, textures, mesh, LOD, physics
```

## Render graph

Ordered passes (extension points):

`environment → lighting → avatar → effects → overlay → present`

Passes should prefer reading a single `:class:`~motion_engine.rendering.context.FrameContext``
instead of long parameter lists.

## Scene graph

```text
SceneGraph
  └── TransformNode (root)
        ├── RenderNode (ground / floor)
        ├── RenderNode (avatar)
        └── TransformNode (lights) → …
```

Today the PyVista path still uses `draw_*` queues for the metallic figure.
The scene graph is the forward structure: future avatars, ground, and lights
attach as nodes; the renderer walks `iter_render_nodes()`.

## Frame lifecycle (formal)

```text
Initialize → Load Assets → Create Scene
    → (per frame) Update → Animate → Render → Present
    → Shutdown
```

Tracked by `:class:`~motion_engine.rendering.lifecycle.RenderLifecycle``.
Hook failures are logged; they must not crash the frame.

## Avatar pipeline

```text
assets/avatars/<name>/avatar.json   # data — never hardcode paths
        ↓
AvatarManifest.load / for_avatar
        ↓
AvatarManager.register / set_active
        ↓
update(frame) → render(backend)
```

Default active avatar remains **ProceduralAvatar** (metallic skeleton).
MetaHuman is manifest-only until Phase 1 — no runtime implementation here.

## Resource ownership

| Owner | Owns |
|-------|------|
| `ResourceManager` | mesh / texture / shader / material caches; hot-reload via `invalidate` |
| `SceneGraph` | node hierarchy (logical) |
| `AvatarManager` | avatar instances + active selection |
| `EnvironmentManager` | active environment preset + StudioEnvironment IBL |
| `LightingManager` | light rig + preset |
| `MaterialLibrary` | named PBR presets |
| `PyVistaRenderer` | VTK/PyVista plotter + draw queues (compat facade) |

Missing textures/meshes/HDRI/materials → **log + fallback**, never crash.

## Threading assumptions

* The renderer and VTK/PyVista plotter are **main-thread only**.
* Resource caches are not thread-safe; load assets on the render thread
  or gate with an external lock before Phase-1 async IO.
* Event bus listeners must not block the frame; keep handlers cheap.

## Extension guide

### Register without modifying core

```python
renderer.register_avatar("metahuman", MetaHumanAvatar)
renderer.register_environment("custom", MyEnvFactory)
renderer.register_material("gold", lambda: PBRMaterial(...))
renderer.register_effect("trails", MyTrailsEffect)
```

Prefer `PluginRegistry` / `Renderer.register_*` over `if/elif` switches.

### Materials / lighting / environment / camera

```python
MaterialLibrary().get("titanium")
LightingManager("clinical").setup(plotter)
EnvironmentManager("presentation").configure_renderer(plotter)
get_camera_profile("cinematic")   # FOV, damping, framing — feeds future camera defaults
get_quality("ultra")              # shadows / MSAA / LOD / AO bundle
```

### Config

Edit `config/rendering.yaml` for quality, presets, shadows, floor, HDRI,
and default materials. `RenderSettings.load()` applies it with safe defaults
if the file is missing.

## Dependency rules

See [dependency_rules.md](dependency_rules.md). Enforced by
`tests/test_dependency_rules.py`.

## Architecture freeze

See [ARCHITECTURE_FREEZE.md](ARCHITECTURE_FREEZE.md). Public imports:

`motion_engine.api.rendering` / `avatar` / `viewer` / `scene`.

## Benchmarks

`python -m benchmarks.run_benchmarks` — see `benchmarks/README.md`.
