# 40 — Phase 1 Architecture

```text
MATLAB Motion Database
        │
        ▼
 Motion Engine (domain)
        │
        ▼
 Retarget Engine (M6)
        │
        ▼
 AnimationPose (M3/M5)
        │
        ▼
 Skinning Runtime (M4)
        │
        ▼
 DeformedMesh → Renderer → Viewer / Studio
        ▲
        │
 DigitalTwinRuntime (M7)  ← lifecycle, session, profiler, validation
```

## Ownership

| Layer | Owns | Must not own |
|-------|------|--------------|
| M2 Skeleton | Hierarchy, bones | Animation, skinning |
| M3 Pose | Bind/Animation poses | Skinning math |
| M4 Skinning | LBS deform | Retarget |
| M5 Animation | Clips/player | Clinical DB |
| M6 Retarget | Mapping → pose | Mesh deform |
| M7 Runtime | Orchestration | Duplicate of above |

## Non-negotiables

- Quaternion-only rotations internally
- Data-driven skeleton / mapping configs
- No circular imports
- Research extensibility without public API redesign
