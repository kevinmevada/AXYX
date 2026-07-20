# 15 — M3 Bind Pose Specification

**Milestone:** M3 — Bind Pose Runtime  
**Code:** `src/motion_engine/rendering/avatar/pose/`  
**Status:** Implemented

---

## Architecture

```text
AvatarSkeleton (structure, M2, immutable)
        │
        ▼ BindPoseFactory
Pose (ABC)
  ├── BindPose         immutable reference / bind / rest
  └── AnimationPose    mutable placeholder (M5)
```

**Structure vs state:** skeleton is hierarchy; bind pose is the undeformed reference state.

Legacy `avatar.bind_pose.BindPose` (XYZ joint map stub) remains unchanged for M1 compatibility.
Runtime bind pose is `pose.BindPose`.

---

## Modules

| File | Role |
|------|------|
| `pose.py` | `Pose` ABC, `BonePose`, `AnimationPose` |
| `bind_pose.py` | Immutable `BindPose` |
| `pose_factory.py` | `BindPoseFactory` / `PoseFactory` |
| `transform_propagation.py` | Deterministic FK |
| `bind_matrix.py` | IBM construction / checks |
| `matrix_utils.py` | Math helpers |
| `pose_validation.py` | Structured diagnostics |
| `pose_statistics.py` | Auto stats |
| `pose_serialization.py` | Debug export |
| `pose_cache.py` | Future-ready cache |
| `coordinate_system.py` | Handedness / units metadata |
| `rest_pose.py` | T/A/imported/custom tags |

---

## Construction rule

Default: authored skeleton **bind worlds** are authoritative. Locals are derived as
`local = inv(parent_world) @ world` so FK is mathematically consistent. IBM prefers
authored values, else `inv(world)`.

---

## Non-goals

Animation playback, skinning, IK, retarget, Viewer/Studio/Rendering API changes,
modifying `AvatarSkeleton`.
