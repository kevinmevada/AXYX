# 25 — M5 Animation Runtime Spec

**Status:** Implemented  
**Package:** `rendering/avatar/animation/`

## Pipeline

```
AnimationClip → AnimationTrack → Keyframes → Interpolator
    → AnimationEvaluator → AnimationPose → M4 SkinningRuntime → DeformedMesh
```

## Core objects

| Object | Role |
|--------|------|
| `AnimationClip` | Immutable clip asset (tracks, markers, events) |
| `AnimationTrack` | Per-bone sparse channel |
| `Keyframe` | time + optional TRS (quat xyzw) |
| `AnimationPlayer` | Clock + evaluate |
| `AnimationController` | Idle/Walk/Run/Jump + crossfade |
| `AnimationEvaluator` | Sample any float time → pose |

## Interpolation

- Translation / scale: linear (step / cubic Hermite supported)
- Rotation: **quaternion SLERP only** (never Euler)

## Loaders (`AnimationFactory`)

- Procedural: `hold_pose`, `wave_clip`, `locomotion_set`
- JSON: `from_json` / `from_dict`
- glTF/GLB: `from_gltf`
- FBX: `from_fbx` (ufbx bake)

## Hard constraints

Does **not** modify M1–M4, Viewer, Studio, or Renderer public APIs.
Consumes `BindPose` / `AnimationPose` (M3) and `SkinningRuntime` (M4).
