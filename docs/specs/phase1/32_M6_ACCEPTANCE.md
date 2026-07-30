# 32 — M6 Acceptance Criteria

M6 is accepted when all of the following hold:

- [x] MATLAB / clinical motion (or synthetic clinical gait) drives avatar poses
- [x] Different skeletons retarget via mapping profiles
- [x] Coordinate systems convert (Z-up ↔ Y-up, handedness, units)
- [x] Scale / proportion compensation produces finite ratios
- [x] Root motion modes: world, in-place, extract
- [x] Joint constraints enforced (soft clamp + hard fail)
- [x] Quaternion normalization validated
- [x] Benchmarks complete (`benchmarks/m6_retarget.py`)
- [x] Certification passes (`certify_m6_retarget.py`)
- [x] Documentation complete (30–34)
- [x] Freeze document written
- [x] Character walk path exists via research-style clinical gait → `AnimationPose` → skinning

## Non-goals (explicit)

- Not a replacement for M5 AnimationPlayer
- Does not rewrite Viewer / Studio / Renderer public APIs
- Does not mutate BindPose / AvatarSkeleton
