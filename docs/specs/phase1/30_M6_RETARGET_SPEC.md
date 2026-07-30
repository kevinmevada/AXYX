# 30 — M6 Motion Retargeting Spec

**Status:** Implemented  
**Package:** `rendering/avatar/retarget/`  
**Version:** 1.0.0

## Purpose

Convert arbitrary skeletal motion into an `AvatarSkeleton` `AnimationPose` while preserving biomechanics. This is **not** an animation player.

```
MATLAB / MoCap / BVH / C3D / FBX / glTF
  → MotionSkeleton + MotionPose
  → RetargetEngine
  → AnimationPose
  → SkinningRuntime (M4)
  → Viewer
```

## Primary API

| Object | Role |
|--------|------|
| `RetargetEngine` | Frame pipeline → `AnimationPose` |
| `RetargetContext` | Prepared mapping / offsets / scales |
| `RetargetSession` | Multi-frame filters + root motion |
| `MappingProfile` | Data-driven bone map |
| `RetargetFactory` | Profiles, synthetic gait, sessions |

## Pipeline

1. Coordinate conversion (handedness, up/forward, units)
2. Skeleton / joint mapping (1:1, 1:N, N:1, optional, virtual)
3. Scale / proportion compensation
4. Constraint solver (limits, locks, preferred axes)
5. Offset solver (bind alignment)
6. Root motion (world / in-place / extract + loop correction)
7. Pose conversion → `AnimationPose`

## Hard constraints

Does **not** modify:

- Motion source data
- `AvatarSkeleton` / `BindPose`
- AnimationRuntime (M5)
- SkinningRuntime (M4)
- Viewer / Renderer / Studio public APIs

Rotations are **quaternion only** (never Euler internally; Euler used only for limit clamping).

## Builtin mapping profiles

- `matlab_clinical_to_metahuman`
- `matlab_clinical_to_army_girl`
- `mixamo_to_metahuman`
- `identity` / `test_two_bone`
- Custom JSON via `MappingFactory.from_json`

## Research extensibility

Designed for clinical gait, neurology, orthopedics, sports biomechanics, robotics, exoskeletons, digital twins, neural retargeting, and foundation motion models without public API breakage.
