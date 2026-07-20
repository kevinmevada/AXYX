# Phase-0.5 — Rendering Architecture Polish

Architecture-only pass before Digital Twin Phase 1.

## Added

* `rendering/context/` — FrameContext, RenderingContext, RenderSettings
* `rendering/resources/` — ResourceManager + caches
* `rendering/scene/` — SceneGraph + nodes
* `rendering/events/` — RenderEventBus
* `rendering/quality/` — low/medium/high/ultra
* `rendering/debug/` — stats, profiler, debug_draw
* `rendering/lifecycle/` — formal Initialize…Shutdown
* `rendering/plugins/` — PluginRegistry + Renderer.register_*
* `rendering/camera/profiles/` — clinical/orbit/presentation/cinematic/analysis
* Lighting / material / environment **presets**
* `config/rendering.yaml`
* `assets/avatars/*/avatar.json` manifests
* Tests: `tests/test_rendering_phase05.py`
* Docs: `docs/architecture/rendering.md` updated

## Compatibility

Public `draw_*` / viewer / camera APIs unchanged. Procedural metallic avatar
remains default. No MetaHuman runtime.
