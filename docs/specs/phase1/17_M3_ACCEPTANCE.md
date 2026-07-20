# 17 — M3 Acceptance Criteria

1. `rendering/avatar/pose/` modules exist as specified.
2. `Pose` ABC with `BindPose` + `AnimationPose` placeholder.
3. `BindPoseFactory.from_skeleton` builds validated immutable bind poses.
4. `AvatarSkeleton` remains immutable / unmodified API.
5. FK propagation deterministic; IBM inverts rest within tolerance.
6. Validation rejects empty / FK-inconsistent poses.
7. `tests/pose` passes; benchmarks run; certification exits 0.
8. Docs `15`–`19` present; Phase 1 README indexed.
9. No Viewer / Studio / Rendering / M1 / M2 public API breaks.
