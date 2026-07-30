# AXYX Digital Twin Runtime (Phase 1 — M7)

Unified research platform integrating M1–M6.

## Pipeline

```
MotionDatabase → Subject → Trial → RetargetEngine → AnimationPose
  → SkinningRuntime → DeformedMesh → Viewer / Measurements
```

## Entry point

`DigitalTwinRuntime` / `RuntimeFactory`

## Presets

- `default`
- `research`
- `debug`
- `benchmark`

## Hard rules

Does not modify frozen public APIs of skeleton, pose, skinning, animation,
retarget, viewer, studio, or renderer.
