# Phase 1 Master Specification — Digital Twin Avatar Runtime

**Status:** Contract (implementation not started)  
**Depends on:** Architecture Freeze `v1.0-architecture` (`docs/architecture/ARCHITECTURE_FREEZE.md`)  
**API surface:** Prefer `motion_engine.api.*` — do not break Viewer or Studio contracts  

This master document is the **Phase 1 contract**. Implementation documents `01`–`09` are executable work packages. If a detail conflicts with this master, **this master wins** until amended.

---

## 1. Objectives

Phase 1 delivers a **Digital Twin avatar runtime** on top of the frozen rendering architecture:

1. Load self-contained avatar packs from `assets/avatars/<name>/` via `avatar.json`.
2. Import skeleton, bind pose, meshes, materials, textures, and LODs.
3. Drive skinned (or procedural) avatars from **AXYX canonical mocap poses**.
4. Retarget from the AXYX clinical skeleton → avatar skeleton with correct scale, coordinates, and rotations.
5. Switch between **procedural** and **digital** avatars at runtime **without** Viewer or Studio code changes.
6. Validate assets and runtime state automatically; ship tests + benchmarks + docs.

**Success statement:** A clinician (or demo) can play mocap through Studio and see either the metallic procedural figure or a skinned digital avatar, swapped via `AvatarManager.set_active`, with identical viewer controls.

---

## 2. Scope

### In scope

| Area | Deliverable |
|------|-------------|
| Asset pipeline | Loaders for manifest, mesh, skeleton, material, texture, LOD |
| Avatar skeleton | Bone / hierarchy / bind pose / transforms |
| Skinning | CPU skinning + GPU interface stub |
| Animation runtime | Clips, player, interpolation, pose cache |
| Retarget engine | Joint / coordinate / scale / rotation / pose mapping |
| Validation | Automated diagnostics + reports |
| Integration | `Avatar` implementations registered with `AvatarManager` |
| Tests | Unit, integration, runtime, regression, performance, visual checklist |
| Docs | This pack + updates to `docs/architecture/rendering.md` |
| Benchmarks | Extend `benchmarks/` for load / skin / retarget / frame times |

### Compatible with existing systems (must preserve)

- `motion_engine.api.*` public surface  
- `Avatar` ABC + `AvatarManager`  
- `PyVistaRenderer` draw_* path for procedural (may coexist)  
- `config/rendering.yaml`, asset IDs, scene graph, render graph, lifecycle  
- Dependency rules (no Qt in avatar; no Studio imports in rendering)

---

## 3. Out of scope

Explicitly **not** Phase 1:

- Studio UI redesign or new panels (beyond using existing avatar switch hooks if any)
- Viewer API changes (public methods stay stable)
- Unreal / OpenGL / Vulkan backends (capability flags only)
- GPU skinning implementation (interface + stub only)
- Full MetaHuman Unreal export pipeline automation
- Physics simulation / cloth / hair
- Facial animation / blendshapes (may reserve manifest fields)
- ECS, DI frameworks, networking, scripting
- Clinical AI / explainability features
- Cloud asset CDN
- Undo/redo, plugin marketplace

---

## 4. Architecture

Phase 1 **extends** `rendering/avatar/` — it does not replace the architecture freeze.

```text
Studio / Viewer  (UNCHANGED public contract)
        ↓
AvatarManager.set_active("procedural" | "metahuman" | …)
        ↓
Avatar.load / update / render     ← ABC from freeze
        ↓
┌───────────────────────────────────────────────────────┐
│  Phase 1 avatar subsystems                            │
│  loader → skeleton → animation → retarget → runtime   │
│  validation                                           │
└───────────────────────────────────────────────────────┘
        ↓
ResourceManager / SceneGraph / RenderGraph / Backend
```

### Principles

1. **Data-driven** — paths only via manifests + stable asset IDs (`avatar.metahuman.default`).
2. **Avatar-agnostic viewer** — no `if metahuman` in viewer/studio.
3. **Canonical AXYX pose in, avatar pose out** — retarget is the boundary.
4. **Fail soft** — missing textures/bones → diagnostics + fallbacks, not crashes.
5. **CPU skinning first** — correct then fast; GPU path reserved.

---

## 5. Data flow

```text
assets/avatars/<id>/avatar.json
        │
        ▼
ManifestLoader ──► Mesh / Skeleton / Material / Texture loaders
        │
        ▼
AvatarSkeleton + BindPose + SkinnedMesh(es) + Materials
        │
AXYX Pose (canonical clinical skeleton)
        │
        ▼
RetargetEngine (joint map → coord → scale → rotation → pose)
        │
        ▼
AnimationRuntime / SkinningRuntime
        │
        ▼
Avatar.render(backend) → SceneGraph RenderNodes → Present
```

Per-frame:

```text
FrameContext
  → AvatarManager.update(axyx_pose_or_clip_frame)
      → Retarget → local bone transforms
      → SkinningRuntime.apply (CPU)
  → AvatarManager.render(backend)
  → RenderGraph → Present
```

---

## 6. Folder structure (target)

### Code

```text
src/motion_engine/rendering/avatar/
    loader/
        avatar_loader.py
        mesh_loader.py
        skeleton_loader.py
        material_loader.py
        texture_loader.py
        manifest_loader.py
    skeleton/
        avatar_skeleton.py
        bone.py
        hierarchy.py
        bind_pose.py
        inverse_bind_matrix.py
        transforms.py
    animation/
        animation_clip.py
        animation_player.py
        animation_controller.py
        pose.py
        pose_cache.py
        interpolation.py
        blend_tree.py
    runtime/
        avatar_runtime.py
        skinning_runtime.py
        animation_runtime.py
    retarget/
        joint_mapper.py
        coordinate_mapper.py
        rotation_mapper.py
        scale_mapper.py
        pose_mapper.py
    validation/
        validator.py
        diagnostics.py
        report.py
```

Existing modules (`avatar.py`, `avatar_manager.py`, `procedural/`, `avatar_manifest.py`) remain; Phase 1 **adds** packages above and wires new `Avatar` subclasses.

### Assets

```text
assets/avatars/
    metahuman/
        avatar.json
        meshes/
        skeleton/
        materials/
        textures/
        animations/
        physics/
        lod/
    procedural/
        avatar.json
    future/
assets/hdri/
assets/environments/
assets/materials/
```

Each avatar pack is **self-contained**. Relative paths in `avatar.json` are relative to that avatar’s root directory.

### Specs (this pack)

```text
docs/specs/phase1/
    00_PHASE1_MASTER_SPEC.md      ← this file
    01_ASSET_PIPELINE.md
    02_AVATAR_SKELETON.md
    03_BIND_POSE.md
    04_SKINNING.md
    05_ANIMATION_RUNTIME.md
    06_RETARGET_ENGINE.md
    07_RUNTIME_VALIDATION.md
    08_TEST_PLAN.md
    09_ACCEPTANCE_CRITERIA.md
```

---

## 7. Public APIs

### Stable (must not break)

```python
from motion_engine.api.avatar import Avatar, AvatarManager, ProceduralAvatar
from motion_engine.api.rendering import PyVistaRenderer, FrameContext
from motion_engine.api.viewer import SkeletonViewer
```

### Phase 1 additions (new, versioned)

Expose via `motion_engine.api.avatar` when stable:

| Symbol | Role |
|--------|------|
| `AvatarManifest` / manifest loader | Already partially present — complete |
| `DigitalAvatar` (name TBD) | Skinned avatar implementing `Avatar` |
| `RetargetEngine` | Canonical → avatar pose |
| `AvatarValidator` | Pre-flight + runtime checks |
| `AvatarRuntime` | Orchestrates load/update/skin |

Internal loaders/skeleton math stay under `rendering.avatar.*` (not public until freeze amendment).

### Registration (no switches)

```python
renderer.register_avatar("metahuman", DigitalAvatar)
manager.set_active("metahuman")
```

---

## 8. Coding standards

- Python 3.11+, type hints, `logging.getLogger(__name__)` — **no `print`**.
- Follow dependency rules (`docs/architecture/dependency_rules.md`).
- Raise `rendering.errors.*` (`AvatarLoadError`, `MeshLoadError`, …) with codes.
- Missing assets → log + graceful fallback / diagnostics; do not crash Studio.
- Prefer asset IDs over filesystem paths in application code.
- Unit tests colocated under `tests/` (not only under avatar/tests — pytest root is `tests/`).
- Optional: `tests/avatar/` package mirroring subsystems.
- No feature flags that require Studio changes; config via `avatar.json` + `config/rendering.yaml` extensions if needed.

---

## 9. Performance targets

Baselines measured with `benchmarks/` (extend harness). Targets are **initial gates**, not hard SLAs:

| Metric | Target (dev machine, procedural or LOD≥1 digital) |
|--------|-----------------------------------------------------|
| Avatar cold load (procedural) | ≤ 50 ms |
| Avatar cold load (digital LOD1, cached meshes) | ≤ 2.0 s |
| Retarget + pose update | ≤ 1.0 ms / frame |
| CPU skinning (LOD1) | ≤ 8.0 ms / frame |
| Full frame (update+skin+submit, offscreen) | ≤ 16.7 ms (60 FPS headroom) |
| Memory (digital LOD1 resident) | Track + report; no unbounded growth across 1000 frames |

Record results in benchmark JSON after each milestone.

---

## 10. Asset requirements

Minimum viable digital pack (MetaHuman / Kili or equivalent):

1. Valid `avatar.json` (schema documented in `01`).
2. Skeleton with bind pose + inverse bind matrices.
3. At least one skinned mesh LOD.
4. Base color (+ optional normal / SRMF) textures or graceful missing-texture fallback.
5. Materials referencing textures by relative path or material preset ID.
6. Optional native animation clip for soak tests.
7. Joint map file or section mapping avatar bones → AXYX canonical names.

Procedural pack remains valid with generator-based mesh (no binary mesh required).

Coordinate system: document source (e.g. UE/Z-up vs AXYX) in manifest; conversion is mandatory in retarget (`06`).

---

## 11. Milestones

| ID | Name | Exit gate |
|----|------|-----------|
| M0 | Spec pack signed off | This folder complete; freeze tag present |
| M1 | Asset pipeline | Manifest + mesh + skeleton + material + texture load; validation |
| M2 | Skeleton + bind pose | Hierarchy + IBM + rest pose reconstruct |
| M3 | Skinning | CPU deform; single-bone rotation visual check |
| M4 | Animation runtime | Native clip playback on avatar skeleton |
| M5 | Retarget | AXYX pose drives digital avatar |
| M6 | Integration | Runtime switch procedural ↔ digital; no viewer/studio edits |
| M7 | Hardening | Full test suite + benchmarks + docs + acceptance (`09`) |

Implement in order M1→M7. Do not start M5 before M2/M3 gates pass.

---

## 12. Deliverables

1. Code under `rendering/avatar/{loader,skeleton,animation,runtime,retarget,validation}/`
2. Self-contained `assets/avatars/metahuman/` layout (migrate from flat cache as needed)
3. `DigitalAvatar` (or equivalent) registered beside `ProceduralAvatar`
4. Tests per `08_TEST_PLAN.md`
5. Benchmark suite updates + collected numbers
6. Updated architecture docs + this spec pack kept current
7. Phase 1 acceptance report checklist (`09`) all checked

---

## 13. Acceptance criteria (summary)

Phase 1 is **complete only when** every item in `09_ACCEPTANCE_CRITERIA.md` passes, including:

- [ ] Avatar manifest loads  
- [ ] Mesh / skeleton / bind pose / textures / materials  
- [ ] Skinning verified  
- [ ] Retarget from AXYX drives runtime animation  
- [ ] Procedural ↔ digital switch at runtime  
- [ ] **No Viewer changes required**  
- [ ] **No Studio changes required**  
- [ ] All tests pass; benchmarks collected; docs updated  

Full checklist: [`09_ACCEPTANCE_CRITERIA.md`](09_ACCEPTANCE_CRITERIA.md).

---

## 14. Spec index

| Doc | Topic |
|-----|--------|
| [01_ASSET_PIPELINE.md](01_ASSET_PIPELINE.md) | Formats, loaders, LOD, validation |
| [02_AVATAR_SKELETON.md](02_AVATAR_SKELETON.md) | Bones, hierarchy, naming |
| [03_BIND_POSE.md](03_BIND_POSE.md) | IBM, rest pose, scale |
| [04_SKINNING.md](04_SKINNING.md) | Weights, CPU/GPU interface |
| [05_ANIMATION_RUNTIME.md](05_ANIMATION_RUNTIME.md) | Clips, playback, blending |
| [06_RETARGET_ENGINE.md](06_RETARGET_ENGINE.md) | Mapping & conversion (heart of Phase 1) |
| [07_RUNTIME_VALIDATION.md](07_RUNTIME_VALIDATION.md) | Automatic diagnostics |
| [08_TEST_PLAN.md](08_TEST_PLAN.md) | Test matrix |
| [09_ACCEPTANCE_CRITERIA.md](09_ACCEPTANCE_CRITERIA.md) | Done definition |

---

## 15. Amendment process

Changes to scope/APIs require:

1. Update this master + affected `01`–`09` docs in the same PR.
2. Note impact on freeze / public API.
3. Do not silently diverge implementation from spec.
