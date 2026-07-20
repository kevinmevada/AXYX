# 14 — M2 Freeze

**Milestone:** M2 — Avatar Skeleton Runtime  
**Tag recommendation:** `v1.2.0` (when release-tagged)  
**Status:** FROZEN upon certification PASS

---

## Freeze statement

The package `motion_engine.rendering.avatar.skeleton` is the baseline runtime
skeleton for Phase 1 digital avatars.

Frozen contracts:

- `AvatarSkeleton` query / traversal / validation / statistics / metadata APIs
- `Bone` / `Transform` field semantics
- `AvatarSkeletonFactory.from_imported` / `from_loaded` / `from_bone_tables`
- Validation error codes (`SKEL_*`)
- Debug serialization helpers (shape may extend additively)

M1 remains frozen: loaders, `models.skeleton` DTOs, Viewer, Studio, Rendering APIs.

---

## Allowed after freeze

- Additive APIs (new methods) behind review
- Bug fixes that preserve behavior
- M3+ consumers (skinning, bind-pose depth, animation) that **import** this package

## Disallowed without new milestone

- Breaking changes to `AvatarSkeleton` / `Bone` fields
- Rewriting M1 import DTOs in place
- Viewer / Studio coupling inside `skeleton/`
- Silent acceptance of invalid hierarchies

---

## Downstream rule

> No subsystem may operate directly on imported `BoneData` hierarchies for
> runtime logic. Convert via `AvatarSkeletonFactory` first.
