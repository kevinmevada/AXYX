# AXYX Motion Retargeting Engine (Phase 1 — M6)

Convert arbitrary skeletal motion into an `AvatarSkeleton` `AnimationPose`
while preserving biomechanics.

## Pipeline

```
Motion Frame
  → Coordinate Conversion
  → Skeleton / Joint Mapping
  → Scale Compensation
  → Constraint Solver
  → Offset Solver
  → Root Motion
  → AnimationPose
  → Skinning Runtime (M4)
```

## Quick start

```python
from motion_engine.rendering.avatar.retarget import RetargetFactory, RootMotionMode

factory = RetargetFactory()
skel, motions = factory.synthetic_gait(n_frames=60)
engine, session = factory.session(skel, avatar_skeleton, bind_pose, profile="matlab_clinical_to_army_girl")
poses = [engine.retarget(m, session.context, session=session) for m in motions]
```

## Hard rules

- Does **not** modify motion data, `AvatarSkeleton`, `BindPose`, animation, or skinning runtimes
- Rotations are **quaternion only** (never Euler internally)
- Mapping profiles are data-driven (builtins + JSON)

## Builtin profiles

- `matlab_clinical_to_metahuman`
- `matlab_clinical_to_army_girl`
- `mixamo_to_metahuman`
- `identity` / `test_two_bone`
