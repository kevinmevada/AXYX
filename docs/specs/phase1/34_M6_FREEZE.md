# 34 — M6 Freeze

**Milestone:** Phase 1 — M6 Motion Retargeting Engine  
**Status:** FROZEN  
**Package:** `src/motion_engine/rendering/avatar/retarget/`  
**Runtime version:** 1.0.0

## Freeze rules

1. Public APIs of M6 (`RetargetEngine`, `RetargetFactory`, `MappingProfile`, `MotionPose`, `MotionSkeleton`) are stable.
2. Do not modify M1–M5 frozen packages to “fix” retarget issues — extend M6 or mapping data.
3. Do not mutate BindPose / AvatarSkeleton / SkinningRuntime from retarget code.
4. Mapping changes ship as JSON / builtin profile data, not hardcoded Python name tables beyond builtins.
5. Certification `certify_m6_retarget.py` must remain PASS before release tags.

## Downstream

M7+ may consume `AnimationPose` streams from `RetargetEngine` for clinical viewers, robotics adapters, and AI motion models.
