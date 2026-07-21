# 20 — M4 Skinning Specification

**Milestone:** M4 — Research-Grade Skinning Runtime  
**Code:** `src/motion_engine/rendering/avatar/skinning/`  
**Status:** Implemented

## Architecture

```text
MeshData + MeshSkin + BindPose/AnimationPose
        → SkinningRuntime → DeformedMesh
```

`MeshSkin` is a first-class asset (WeightTable + BonePalette + metadata), not
embedded exclusively in the mesh — enabling multi-rig / LOD / research comparisons.

## Algorithms

| Algorithm | Status |
|-----------|--------|
| Linear Blend Skinning | **Production** |
| Dual Quaternion | Interface (`SkinningNotSupportedError`) |
| Center of Rotation | Interface (`SkinningNotSupportedError`) |

## Non-goals

Modify M1–M3, Viewer, Studio, Rendering APIs. GPU skinning (interface only).
