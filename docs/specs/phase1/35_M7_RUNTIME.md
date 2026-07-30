# 35 — M7 Digital Twin Runtime

**Status:** Implemented  
**Package:** `rendering/runtime/`  
**Version:** 1.0.0

## Purpose

Integrate frozen M1–M6 into one research-grade platform. M7 adds **no** major new animation/skinning features — it orchestrates lifecycle, session, pipeline, profiling, validation, and certification.

## Pipeline

```
MotionDatabase → Subject → Trial → RetargetEngine → AnimationPose
  → SkinningRuntime → DeformedMesh → Viewer / Measurements
```

## Primary API

| Object | Role |
|--------|------|
| `DigitalTwinRuntime` | One-click research runtime |
| `RuntimeFactory` | Presets: default / research / debug / benchmark |
| `RuntimeManager` | Lifecycle + shared services |
| `RuntimePipeline` | Frame orchestration |
| `RuntimeSession` | Subject / trial / avatar / mapping |

## Hard rules

Does **not** modify public APIs of skeleton, pose, skinning, animation, retarget, viewer, studio, renderer, or motion database.
