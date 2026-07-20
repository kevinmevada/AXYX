# 01 — Asset Pipeline

**Parent:** [00_PHASE1_MASTER_SPEC.md](00_PHASE1_MASTER_SPEC.md)  
**Milestone:** M1  
**Code target:** `rendering/avatar/loader/`

---

## 1. Purpose

Load a self-contained avatar pack into memory structures used by skeleton, skinning, and runtime — without hardcoding paths in Viewer/Studio.

---

## 2. Supported formats

| Kind | Formats (Phase 1) | Notes |
|------|-------------------|--------|
| Manifest | JSON (`avatar.json`) | Required |
| Mesh | GLB, GLTF, NPZ (cached), optional FBX | Prefer GLB/GLTF or existing NPZ caches; FBX via optional dependency |
| Skeleton | JSON hierarchy, GLTF skins, NPZ/sidecar | Must yield bones + IBM |
| Textures | PNG, JPEG; TGA best-effort | Missing → flat color fallback |
| Materials | JSON / manifest section / preset ID | May reference `MaterialLibrary` presets |
| Animations | GLTF clips, future JSON tracks | Optional for M1; required for M4 soak |
| LOD | Multiple mesh files or LOD array in manifest | Select by quality profile |

**Non-goals:** USD, Alembic, raw Unreal `.uasset` runtime load.

---

## 3. Avatar manifest (`avatar.json`)

### Required fields

```json
{
  "schema_version": "1.0.0",
  "name": "metahuman",
  "display_name": "…",
  "type": "metahuman",
  "asset_id": "avatar.metahuman.default",
  "coordinate_system": {
    "up": "z",
    "forward": "x",
    "units": "cm",
    "source": "unreal"
  },
  "skeleton": { },
  "mesh": { },
  "materials": { },
  "textures": { },
  "lod": [ ],
  "retarget": { "joint_map": "skeleton/joint_map.json" }
}
```

### Conventions

- All relative paths resolve against the avatar root (`assets/avatars/<name>/`).
- Prefer stable `asset_id` matching `rendering.assets.asset_ids`.
- Procedural avatars may omit binary meshes and set `"mesh": { "generator": "…" }`.

### Loader

`manifest_loader.py`:

- `load_manifest(path | asset_id) -> AvatarManifest`
- Schema validation (required keys, types)
- On failure → `AvatarLoadError` + diagnostics (no crash of host app if called via safe API)

---

## 4. Module responsibilities

| Module | Responsibility |
|--------|----------------|
| `manifest_loader.py` | Parse + validate `avatar.json` |
| `mesh_loader.py` | Vertices, faces, normals, UVs, skin weights, joint indices |
| `skeleton_loader.py` | Bones, parents, local rest transforms, IBM |
| `material_loader.py` | PBR params + texture bindings |
| `texture_loader.py` | Image → ResourceManager cache |
| `avatar_loader.py` | Orchestrates all loaders → `LoadedAvatarAssets` bundle |

### `avatar_loader` flow

```text
resolve asset_id / path
  → manifest
  → skeleton
  → meshes (selected LOD)
  → textures (referenced)
  → materials
  → optional animations
  → run AssetValidator (07)
  → return LoadedAvatarAssets
```

Use `ResourceManager` for mesh/texture caches (dedupe, invalidate for hot reload later).

---

## 5. Texture loading

- Keys: stable IDs or relative paths from manifest.
- Cache key: `f"{avatar_name}:{rel_path}"`.
- Missing file → log warning, return 1×1 fallback texture (neutral gray or magenta debug if `debug` flag).
- sRGB vs linear: base color sRGB; normal/data maps linear (document in material).

---

## 6. Material loading

- Resolve either:
  - Explicit PBR block in manifest, or
  - Preset ID (`material.graphite`) via `MaterialLibrary.get`.
- Bind texture slots: `base_color`, `normal`, `orm`/`srmf`, `scatter` (optional).
- Missing slot → leave unbound; shader/path uses defaults.

---

## 7. Skeleton loading

Produce structures defined in `02` / `03`:

- Ordered bone list + parent indices  
- Local rest transform (T, R, S)  
- Inverse bind matrices (4×4)  
- Name → index map  

Validate unique names and single root (or documented multi-root with synthetic root).

---

## 8. Mesh loading

Per mesh / LOD:

| Attribute | Required |
|-----------|----------|
| positions | yes |
| indices / faces | yes |
| normals | preferred (generate if missing) |
| uvs | if textured |
| joint_indices | for skinned |
| joint_weights | for skinned |
| material_id | yes |

Skinning attributes validated per `04` (influence count, normalization).

---

## 9. LOD handling

- Manifest `lod[]` lists levels with mesh paths and optional vertex counts.
- Selection: `RenderSettings.quality` / `QualityProfile.lod_bias` → choose LOD index.
- Runtime may keep only active LOD resident in Phase 1 (no streaming required).
- Procedural: LOD may mean radial/template resolution only.

---

## 10. Asset validation (pipeline stage)

Before runtime handoff, check:

- Manifest schema  
- All referenced files exist **or** recorded as optional with fallback  
- Skeleton bone count > 0  
- Skinned mesh influences reference valid bone indices  
- No duplicate bone names  
- Units / coordinate_system fields present  

Emit `ValidationReport` (`07`). Severity: `error` blocks load; `warning` allows load.

---

## 11. Error handling

| Condition | Behavior |
|-----------|----------|
| Missing manifest | `AvatarLoadError` |
| Missing required mesh | `MeshLoadError` |
| Missing texture | warning + fallback |
| Unsupported format | clear error listing supported formats |
| Partial FBX without dependency | skip FBX; prefer GLB/NPZ |

---

## 12. Acceptance for M1

- [ ] `avatar.procedural.default` and `avatar.metahuman.default` resolve  
- [ ] Manifest round-trip parse  
- [ ] Mesh + skeleton load from metahuman pack (or documented NPZ cache)  
- [ ] Texture miss does not crash  
- [ ] Unit tests in test plan § Asset Loading  
