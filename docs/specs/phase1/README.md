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
