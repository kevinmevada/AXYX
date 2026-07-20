# Architecture Freeze — Rendering v1.0

Status: **READY TO FREEZE**

Suggested git tag: `v1.0-architecture`

This documents the freeze checklist before Phase 1 (Digital Twin Runtime).
Do not continue polishing architecture — ship product value next.

## Checklist

| Item | Status |
|------|--------|
| Stable public APIs (`motion_engine.api.*`) | ✅ |
| Interface definitions (`rendering.interfaces`) | ✅ |
| Dependency rules (+ import test) | ✅ |
| Resource management | ✅ |
| Scene graph | ✅ |
| Render graph | ✅ |
| Context objects | ✅ |
| Event system | ✅ |
| Plugin registry | ✅ |
| Lifecycle management | ✅ |
| Configuration (`config/rendering.yaml`) | ✅ |
| Asset manifests + stable asset IDs | ✅ |
| Testing | ✅ |
| Documentation | ✅ |
| Benchmark harness (`benchmarks/`) | ✅ |
| Capability reporting | ✅ |
| Renderer state machine | ✅ |
| Error codes (`rendering.errors`) | ✅ |
| Standardized performance metrics | ✅ |
| Serialization stubs (reserved) | ✅ |

## Public API

```python
from motion_engine.api import API_VERSION
from motion_engine.api.rendering import PyVistaRenderer, RenderSettings, SceneGraph
from motion_engine.api.avatar import AvatarManager, ProceduralAvatar
from motion_engine.api.viewer import SkeletonViewer
from motion_engine.api.scene import MaterialLibrary, LightingManager, get_camera_profile
```

`API_VERSION == "1.0.0"`.

## What not to add before Phase 1

ECS, DI frameworks, job schedulers, networking, scripting, custom shader
languages, plugin marketplaces, undo/redo.

## Next milestone

**Phase 1** — Digital Twin Avatar Runtime.

Implementation contract: [`docs/specs/phase1/`](../specs/phase1/README.md).

Do not polish architecture further. Build against the Phase 1 spec pack
(asset pipeline → bind pose → skinning → retarget → acceptance).
