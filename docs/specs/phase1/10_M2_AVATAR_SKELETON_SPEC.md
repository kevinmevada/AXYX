# 10 — M2 Avatar Skeleton Specification

**Parent:** [00_PHASE1_MASTER_SPEC.md](00_PHASE1_MASTER_SPEC.md)  
**Milestone:** M2 — Avatar Skeleton Runtime  
**Code:** `src/motion_engine/rendering/avatar/skeleton/`  
**Status:** Implemented

---

## 1. Purpose

Provide the **canonical runtime skeleton** for digital avatars. After M2, every
downstream subsystem (bind pose, skinning, animation, retarget, analytics,
biomechanics) consumes `AvatarSkeleton` from this package — never raw M1 import DTOs.

---

## 2. Dual representation (intentional)

| Layer | Type | Location | Role |
|-------|------|----------|------|
| Import DTO (M1, frozen) | `models.skeleton.AvatarSkeleton` / `BoneData` | `models/skeleton.py` | Immutable load output |
| Runtime (M2) | `skeleton.AvatarSkeleton` / `Bone` | `skeleton/` | Authoritative hierarchy + queries |

Conversion: `AvatarSkeletonFactory.from_imported(...)` / `from_loaded(...)`.

Asset pipeline loaders are **not** modified.

---

## 3. Package layout

```text
skeleton/
  avatar_skeleton.py   # AvatarSkeleton
  bone.py              # Bone
  transforms.py        # Transform, matrix/quat ops, FK propagation
  hierarchy.py         # children, LCA, paths, cycle detection
  lookup.py            # O(1) name/index maps
  traversal.py         # DFS / BFS / post / leaves / root→leaf
  validation.py        # structured diagnostics
  statistics.py        # automatic hierarchy stats
  metadata.py          # coordinate system, units, provenance
  serialization.py     # debug JSON / tree (not persistence)
  bind_data.py         # rest-world + IBM buffers
  factory.py           # M1 → M2 bridge
  constants.py / types.py / exceptions.py
```

---

## 4. Bone model

Each `Bone` stores: id, index, name, parent, children, local/rest/world transforms,
inverse bind, TRS accessors, flags, metadata, optional user data.

Bones are **immutable** after construction. World rest updates via
`AvatarSkeleton.rebuild_world_rest()` (returns a new skeleton).

---

## 5. Transforms

- Matrices: `float64` `(4,4)`, column vectors, `world = parent_world @ local`
- Quaternions: **xyzw**, unit length
- Composition: `T @ R @ S`

---

## 6. API surface (runtime)

Lookup: `find`, `exists`, `index_of`, `parent`, `children`, `ancestors`,
`descendants`, `siblings`, `root`, `is_leaf`, `is_root`, `path`, `depth`,
`height`, `common_ancestor`

Traversal: DFS pre/post, BFS, leaves, root→leaf paths, topological FK order

Rest/bind: `rest_local`, `rest_world`, `inverse_bind`, `rebuild_world_rest`

---

## 7. Validation

Errors: empty, duplicate names/ids, bad parents, cycles, orphans, NaN/Inf,
singular matrices, zero scale, missing IBM (when required)

Warnings: multiple roots (policy), non-uniform scale, extreme depth (>256)

---

## 8. Non-goals (M2)

- Animation pose buffers
- Skinning / LBS
- Retarget joint maps
- Viewer / Studio / Rendering API changes
- Changes to M1 loaders or public M1 API contracts
