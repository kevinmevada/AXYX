# Phase 1 Specification Pack

**Digital Twin Avatar Runtime** — implementation contract for AXYX Phase 1.

> Architecture is frozen (`docs/architecture/ARCHITECTURE_FREEZE.md`).  
> These specs define **what to build next**, not further restructuring.

## Documents

| # | File | Role |
|---|------|------|
| 00 | [00_PHASE1_MASTER_SPEC.md](00_PHASE1_MASTER_SPEC.md) | **Master contract** — scope, APIs, milestones |
| 01 | [01_ASSET_PIPELINE.md](01_ASSET_PIPELINE.md) | Manifests, loaders, LOD |
| 02 | [02_AVATAR_SKELETON.md](02_AVATAR_SKELETON.md) | Bones, hierarchy, naming |
| 03 | [03_BIND_POSE.md](03_BIND_POSE.md) | IBM, rest pose (critical) |
| 04 | [04_SKINNING.md](04_SKINNING.md) | CPU LBS + GPU stub |
| 05 | [05_ANIMATION_RUNTIME.md](05_ANIMATION_RUNTIME.md) | Clips, playback, pose cache |
| 06 | [06_RETARGET_ENGINE.md](06_RETARGET_ENGINE.md) | **Heart of Phase 1** |
| 07 | [07_RUNTIME_VALIDATION.md](07_RUNTIME_VALIDATION.md) | Diagnostics |
| 08 | [08_TEST_PLAN.md](08_TEST_PLAN.md) | Test matrix |
| 09 | [09_ACCEPTANCE_CRITERIA.md](09_ACCEPTANCE_CRITERIA.md) | Done definition |
| 10 | [10_M2_AVATAR_SKELETON_SPEC.md](10_M2_AVATAR_SKELETON_SPEC.md) | **M2** runtime skeleton (implemented) |
| 11 | [11_M2_TEST_PLAN.md](11_M2_TEST_PLAN.md) | M2 tests / benches / cert |
| 12 | [12_M2_ACCEPTANCE.md](12_M2_ACCEPTANCE.md) | M2 acceptance |
| 13 | [13_M2_FINAL_AUDIT.md](13_M2_FINAL_AUDIT.md) | M2 audit |
| 14 | [14_M2_FREEZE.md](14_M2_FREEZE.md) | M2 freeze |
| 15 | [15_M3_BIND_POSE_SPEC.md](15_M3_BIND_POSE_SPEC.md) | **M3** bind pose runtime |
| 16 | [16_M3_TEST_PLAN.md](16_M3_TEST_PLAN.md) | M3 tests / benches / cert |
| 17 | [17_M3_ACCEPTANCE.md](17_M3_ACCEPTANCE.md) | M3 acceptance |
| 18 | [18_M3_FINAL_AUDIT.md](18_M3_FINAL_AUDIT.md) | M3 audit |
| 19 | [19_M3_FREEZE.md](19_M3_FREEZE.md) | M3 freeze |
| — | [M2_M3_FREEZE_REPORT.md](M2_M3_FREEZE_REPORT.md) | **M2+M3 joint freeze (approved)** |
| 20 | [20_M4_SKINNING_SPEC.md](20_M4_SKINNING_SPEC.md) | **M4** skinning runtime |
| 21 | [21_M4_TEST_PLAN.md](21_M4_TEST_PLAN.md) | M4 tests / benches / cert |
| 22 | [22_M4_ACCEPTANCE.md](22_M4_ACCEPTANCE.md) | M4 acceptance |
| 23 | [23_M4_FINAL_AUDIT.md](23_M4_FINAL_AUDIT.md) | M4 audit |
| 24 | [24_M4_FREEZE.md](24_M4_FREEZE.md) | M4 freeze |

### Milestone freeze docs (M1)

| File | Role |
|------|------|
| [M1_FINAL_AUDIT_FREEZE.md](M1_FINAL_AUDIT_FREEZE.md) | M1 freeze audit |
| [M1_IMPLEMENTATION_NOTES.md](M1_IMPLEMENTATION_NOTES.md) | M1 notes |

## How to use

1. Read **00** end-to-end before coding.  
2. Implement one milestone (M1→M7) at a time using the matching doc.  
3. Do not expand scope past **00 §3 Out of scope**.  
4. Check boxes in **09** only with test/benchmark evidence.  
5. Prefer prompts that attach a **single** doc (`01`…`07`) plus the master for context.

## Non-negotiables

- No Viewer / Studio API changes required for Phase 1 completion  
- Procedural avatar remains available; digital is additive  
- Data-driven paths via `avatar.json` + stable asset IDs  
