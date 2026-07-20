# 05 — Animation Runtime

**Parent:** [00_PHASE1_MASTER_SPEC.md](00_PHASE1_MASTER_SPEC.md)  
**Milestone:** M4 (native clips); M5+ driven primarily by retargeted AXYX poses  
**Code target:** `rendering/avatar/animation/`, `runtime/animation_runtime.py`

---

## 1. Purpose

Generate time-varying local bone poses for an `AvatarSkeleton`: from native clips **or** from external pose streams (retarget output).

Primary production path for clinical use: **AXYX mocap → retarget → pose** (`06`). Native clips validate skinning and provide soak tests.

---

## 2. Animation clips

```text
AnimationClip
  name: str
  duration_s: float
  ticks_per_second / sample_rate
  channels: dict[bone_name, Track]
Track
  times: float[]
  translations?: Vec3[]
  rotations?: Quat[]
  scales?: Vec3[]
```

Load from GLTF animations or JSON. Reuse concepts from `motion_engine.animation_clip` where possible without coupling Studio to avatar internals.

---

## 3. Pose generation

`Pose` (`animation/pose.py`):

- `local_transforms: list[Transform]` aligned to skeleton indices  
- `world_transforms: list[Mat4]` (optional cache)  
- Methods: `set_local`, `recompute_world(skeleton)`

Sources:

1. Sampled clip at time `t`  
2. Retargeted pose from AXYX  
3. Bind pose (reset)

---

## 4. Interpolation

- Translation / scale: linear  
- Rotation: **slerp** (quaternion)  
- Times outside key range: clamp or wrap per clip loop mode  
- Missing channel: hold bind-local for that component  

`interpolation.py` owns sample math.

---

## 5. Blending

Phase 1 minimum:

- `BlendTree` or simple two-pose lerp/slerp by weight `α ∈ [0,1]`  
- Optional: fade between clip and retarget stream  

Full blend graphs are out of scope beyond a thin `blend_tree.py` stub if unused.

---

## 6. Playback

`AnimationPlayer`:

| Control | Behavior |
|---------|----------|
| `play()` / `pause()` / `stop()` | Standard |
| `time` / `seek(t)` | Seconds |
| `speed` | Scalar (negative = reverse, optional) |
| `loop` | bool |
| `update(dt)` | Advance + sample → Pose |

`AnimationController`: higher-level state (idle clip vs retarget-driven). Retarget mode disables clip sampling or layers under it.

---

## 7. Pose cache

`PoseCache`:

- Reuse world matrix buffers  
- Dirty flags when local changes  
- Avoid realloc each frame  

Metrics: `animation_ms`, `update_ms`.

---

## 8. Runtime update loop

```text
AvatarRuntime.update(frame_ctx, axyx_pose | None):
  if retarget_enabled and axyx_pose:
      pose = RetargetEngine.map(axyx_pose)
  elif player.playing:
      pose = player.update(frame_ctx.delta_time)
  else:
      pose = bind_pose
  pose.recompute_world(skeleton)
  skinning.apply(mesh, skeleton, pose.world)
```

Must integrate with existing `Avatar.update(frame)` ABC.

---

## 9. Acceptance for M4

- [ ] Clip loads and loops  
- [ ] Speed control works  
- [ ] Interpolation stable (no quat flips in tests)  
- [ ] Native animation plays on digital avatar (visual)  
- [ ] Pose cache shows stable memory over 1000 frames  

M5 acceptance depends on retarget feeding this same pose path.
