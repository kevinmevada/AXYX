# 12 — M2 Acceptance Criteria

M2 is accepted when **all** of the following hold:

1. `rendering/avatar/skeleton/` implements the specified modules.
2. `AvatarSkeleton` is the canonical runtime object with hierarchy, lookup,
   traversal, validation, statistics, metadata, and debug serialization.
3. `AvatarSkeletonFactory` converts M1 `models.skeleton.AvatarSkeleton` without
   mutating import DTOs or changing asset pipeline loaders.
4. Bone lookup is O(1); traversal/validation are O(n).
5. Validation rejects empty, cyclic, duplicate-name, and broken-parent skeletons
   with structured diagnostics (never silent).
6. `tests/skeleton/` unit suite passes.
7. `benchmarks/m2_avatar_skeleton.py` runs and writes results.
8. `certify_m2_avatar_skeleton.py` exits 0 (Overall PASS).
9. No Viewer / Studio / Rendering public API / M1 loader contract changes.
10. No circular imports between `models.skeleton` and `skeleton` runtime.
11. Documentation `10`–`14` present under `docs/specs/phase1/`.
