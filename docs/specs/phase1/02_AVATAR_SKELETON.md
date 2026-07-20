# 02 — Avatar Skeleton

**Parent:** [00_PHASE1_MASTER_SPEC.md](00_PHASE1_MASTER_SPEC.md)  
**Milestone:** M2  
**Code target:** `rendering/avatar/skeleton/`

---

## 1. Purpose

Define the runtime skeleton representation for digital (and, where useful, procedural) avatars: bones, hierarchy, transforms, naming, and validation.

Related: bind pose details in [`03_BIND_POSE.md`](03_BIND_POSE.md). Canonical AXYX skeleton remains `motion_engine.skeleton` / `SkeletonDefinition` — Phase 1 avatar skeleton is the **target** of retargeting.

---

## 2. Bone representation

```text
Bone
  index: int
  name: str
  parent_index: int | None   # None = root
  children: list[int]
  local_rest: Transform      # bind / rest local TRS
  world_rest: Transform      # computed
  inverse_bind: Mat4         # see 03
```

### Transform

```text
Transform
  translation: Vec3
  rotation: Quat             # normalized
  scale: Vec3                # prefer uniform; flag non-uniform
```

Storage: NumPy arrays; column-major 4×4 matrices consistent with engine convention (document in `transforms.py`).

---

## 3. Hierarchy

- Directed tree (or forest with synthetic `armature_root`).
- `hierarchy.py`: build children lists, depth-first order, topological order for FK.
- No cycles — validator must reject cycles.
- Depth limit warning if depth > 256 (sanity).

---

## 4. Bind pose

Bind / rest pose is the reference pose used for skinning IBM. Spec: [`03_BIND_POSE.md`](03_BIND_POSE.md).

`AvatarSkeleton` must expose:

- `rest_local[i]`, `rest_world[i]`
- `inverse_bind[i]`
- `rebuild_world_rest()` after load

---

## 5. Local / world transforms

**Forward kinematics (runtime pose):**

```text
world[i] = world[parent] @ local[i]
```

**Rest:**

```text
world_rest[i] = world_rest[parent] @ local_rest[i]
```

Root: `world = local`.

Pose buffers live in `animation/pose.py`; skeleton owns rest + IBM.

---

## 6. Coordinate systems

Avatar skeleton stores bones in **avatar/source space** (e.g. Unreal: Z-up, cm).

Conversion to AXYX / renderer space happens in:

- Import-time option (bake into rest), **or**
- Retarget `coordinate_mapper` (`06`)

Manifest `coordinate_system` is authoritative. Do not assume identity.

AXYX clinical convention (document actual engine convention in implementation notes): right-handed; Z-up for current studio viewer unless specified otherwise in `config/coordinate_system.yaml`.

---

## 7. Bone lookup

```python
skeleton.index_of("pelvis") -> int
skeleton.bone("pelvis") -> Bone
skeleton.try_bone("missing") -> None
```

- Lookups are case-sensitive by default; optional alias table in joint map.
- O(1) name→index dict built at load.

---

## 8. Joint naming

### Avatar-native names

Keep original names from asset (e.g. `pelvis`, `thigh_l`, `spine_01`).

### Canonical AXYX names

Clinical / mocap names from `config/skeleton_definition.yaml` (e.g. 15-point set for procedural).

### Mapping

Never rename avatar bones in-place for retarget. Mapping is data in `retarget/joint_map` (`06`).

---

## 9. Skeleton validation

Must detect:

| Check | Severity |
|-------|----------|
| Empty skeleton | error |
| Duplicate names | error |
| Invalid parent index | error |
| Cycles | error |
| Multiple roots without synthetic root | warning/error per policy |
| Non-uniform rest scale | warning |
| Missing IBM | error for skinned avatars |
| Detached bones (unreachable from root) | error |

---

## 10. Modules

| File | Role |
|------|------|
| `bone.py` | Bone dataclass |
| `transforms.py` | TRS ↔ matrix, quat ops |
| `hierarchy.py` | Tree build, walk, FK order |
| `avatar_skeleton.py` | Aggregate + lookup |
| `bind_pose.py` / `inverse_bind_matrix.py` | See 03 |

---

## 11. Relationship to procedural avatar

Procedural metallic figure may continue using AXYX `Skeleton` / joint positions directly without full IBM skinning. Digital avatars **must** use `AvatarSkeleton`.

Shared: naming discipline and validation utilities where practical.

---

## 12. Acceptance for M2 (skeleton portion)

- [ ] Load metahuman (or test) skeleton into `AvatarSkeleton`  
- [ ] Parent–child relationships verified  
- [ ] Name lookup works  
- [ ] Validation rejects duplicate names / cycles  
- [ ] Unit tests per `08` § Skeleton  
