# AXYX Phase 1 — M2 + M3 Architecture Freeze Report

**Date:** 2026-07-20  
**Scope:** Avatar Skeleton Runtime (M2) + Bind Pose Runtime (M3)  
**Audit type:** Final architecture freeze

---

## Verdict

# M2 + M3 APPROVED FOR FREEZE

Prior blockers **B1/B2** (shared `BonePose` / shared NumPy buffers in
`AnimationPose.from_pose`) are **resolved**. Ownership certification and pose
regression tests pass. Packages below are **frozen**.

---

## Frozen packages

- `src/motion_engine/rendering/avatar/skeleton/`
- `src/motion_engine/rendering/avatar/pose/`

**Rule:** Future milestones (M4–M7) may **consume** these APIs. They shall **not**
modify public APIs except for verified bug fixes. No feature additions, no
refactoring, no redesigns.

---

## Blocker resolution

| ID | Issue | Fix |
|----|-------|-----|
| B1 | `from_pose` used `list(pose.bones)` (shared objects) | `BonePose.clone()` + `[b.clone() for b in pose.bones]` |
| B2 | Shared ndarray / metadata aliases | Clone copies every matrix and `dict(metadata)` |

**Measured after fix:**

```text
anim.bones[i] is bind.bones[i]                     → False
anim.local/world/rest/ibm is bind.*                → False
mutate anim matrices/metadata → bind unchanged     → True
python tests/certification/test_pose_ownership.py  → PASS
pytest tests/pose                                  → 42 passed
```

---

## Grades

| Area | Grade |
|------|-------|
| Architecture | **A** |
| Code Quality | **A** |
| Testing | **A** |
| Performance | **A** |
| Documentation | **A** |
| Research Readiness | **A** |
| **Overall** | **A** |

---

## Architecture summary

```text
M1 Imported DTO (frozen)
        │ AvatarSkeletonFactory
        ▼
AvatarSkeleton          ← structure (M2, immutable)
        │ BindPoseFactory
        ▼
BindPose (Pose)         ← reference state (M3, immutable)
        │ AnimationPose.from_pose (deep clone)
        ▼
AnimationPose (Pose)    ← independent mutable state (M5-ready)
```

- No Viewer / Studio coupling in frozen packages  
- No circular imports (`skeleton` ↛ `pose`)  
- Legacy `avatar.bind_pose.BindPose` stub remains distinct  

---

## Completed milestones

| Milestone | Package | Status |
|-----------|---------|--------|
| M2 Avatar Skeleton Runtime | `skeleton/` | **FROZEN** |
| M3 Bind Pose Runtime | `pose/` | **FROZEN** |

---

## Test / certification evidence

| Gate | Result |
|------|--------|
| `pytest tests/pose` | **42 passed** |
| `certify_m2_avatar_skeleton.py` | **PASS** (exit 0) |
| `certify_m3_bind_pose.py` | **PASS** (exit 0) |
| `test_pose_ownership.py` | **PASS** (exit 0) |

---

## Benchmarks

Artifacts under `benchmarks/results/`:

- `m2_avatar_skeleton.{json,csv,md}`
- `m3_bind_pose.{json,csv,md}`

Timing via `time.perf_counter_ns()`; stats include min/max/mean/median/stdev/p95.

---

## Approved API surface (frozen)

**M2:** `AvatarSkeleton`, `Bone`, `AvatarSkeletonFactory`, hierarchy/lookup/traversal/validation/statistics/serialization exports.

**M3:** `Pose`, `BonePose`, `BindPose`, `AnimationPose`, `BindPoseFactory` / `PoseFactory`, validation/serialization/`PoseCache` exports.

---

## Accepted technical debt (deferred; not freeze blockers)

| ID | Debt |
|----|------|
| TD-M1 | Full-res TGA decode / warm≈cold loads |
| TD-CI | ruff/mypy/black not in current venv/CI |
| TD-API | Runtime types not yet on `api.avatar` |
| TD-ANIM | `set_local_matrix` does not auto-FK (M5) |
| TD-REST | T/A-pose geometric generators (kinds only) |
| TD-PERF | Pose construction cost (validation/copies) |
| TD-VIEW | Matrix property accessors remain writable views **within** a single pose owner (cross-pose isolation is guaranteed by clone) |

---

## Future milestones

Build **on** these frozen interfaces:

- M4 Skinning  
- M5 Animation  
- M6 Retarget  
- M7 Validation / acceptance depth  

---

## Sign-off

**M2 + M3 APPROVED FOR FREEZE**  
Baseline for remaining Phase 1 development.
