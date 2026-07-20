# Phase 2 — Digital Twin Avatar Layer

## Architecture

```
Motion Data → Skeleton Reconstruction → Retargeting (YAML) → Avatar Renderer
                                                              ├── metallic (fallback)
                                                              ├── kili (default)
                                                              └── future avatars
```

The motion engine never imports avatar mesh code. Studio / `SkeletonViewer`
own the active `:class:`AvatarBackend``.

## KILI assets (inspected)

| Asset | Role |
|-------|------|
| `SKM_Kili_BodyMesh.FBX` | 4 LODs, 342 bones, full LBS skinning, **no blend shapes** |
| `Kili_Outfits.FBX` | Clothing meshes, same UE5 skeleton |
| `T_Body_BC_VT.TGA` | Base color |
| `T_Body_N_VT.TGA` | Normals |
| `T_Body_SRMF_VT.TGA` | Specular / Roughness / Metallic / AO packed |
| `T_Body_Scatter_VT.TGA` | Subsurface scatter |

**Not present in export:** hair strands, PhysicsAsset, facial morph targets.

## Runtime cache

```
scripts/preprocess_kili_lod.py <lod>
scripts/preprocess_kili_textures.py
```

Produces `KILI/cache/body_lod*.npz`, `skeleton.json`, PNG textures.

## Config

- `config/avatars.yaml` — default avatar + registry
- `config/retarget_kili.yaml` — AXYX → Kili bone map (no hardcoded names in Python)
- `KILI/ASSET_MANIFEST.yaml` — asset inventory

## Swap avatars

```python
SkeletonViewer(avatar="metallic")  # stick figure
SkeletonViewer(avatar="kili")      # digital human (default via YAML)
```

## Phase 2 status

| Goal | Status |
|------|--------|
| Avatar-swappable renderer | Done |
| Metallic preserved as fallback | Done |
| YAML skeleton mapping | Done |
| Skinned body + PBR albedo | Done (LOD cache) |
| Hair / cloth sim / face morphs / secondary physics | Blocked — assets not in KILI export |
| Film-quality IBL / SSR / DoF | Partial — existing studio PBR lights; extend next |
