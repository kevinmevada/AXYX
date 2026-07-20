# 19 — M3 Freeze

**Milestone:** M3 — Bind Pose Runtime  
**Status:** FROZEN upon certification PASS  
**Tag recommendation:** `v1.3.0`

## Frozen contracts

- `Pose` / `BonePose` / `BindPose` / `AnimationPose` semantics
- `BindPoseFactory.from_skeleton` / `identity_bind` / `animation_pose_from_bind`
- Validation codes `POSE_*`
- Debug serialization helpers (additive extension allowed)

## Downstream rule

Skinning (M4), animation (M5), retarget (M6), and IK must consume `Pose`
(typically `BindPose` as reference). Do not invent parallel bind representations.

## Disallowed without new milestone

- Breaking `Pose` method contracts
- Mutating `AvatarSkeleton` from pose code
- Coupling pose package to Viewer/Studio
