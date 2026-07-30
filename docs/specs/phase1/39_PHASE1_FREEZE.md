# 39 — Phase 1 Freeze

**Status:** FROZEN  
**Phase version:** 1.0.0  
**Runtime package:** `src/motion_engine/rendering/runtime/`

## Freeze rules

1. Public APIs of M1–M7 are stable.
2. Breaking changes require a new phase (Phase 2+).
3. Mapping / config / preset data may evolve without breaking Python APIs.
4. `certify_phase1.py` must remain PASS on release tags.
5. Do not mutate BindPose / AvatarSkeleton from orchestration code.

## Downstream

Phase 2 may add clinical dashboards, multi-avatar scenes, GPU skinning, and AI motion models on top of this frozen runtime.
