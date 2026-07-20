# 08 — Test Plan

**Parent:** [00_PHASE1_MASTER_SPEC.md](00_PHASE1_MASTER_SPEC.md)  
**Code target:** `tests/` (recommended layout below)

---

## 1. Principles

- Every Phase 1 module has automated coverage before milestone exit.  
- Prefer deterministic synthetic fixtures; use real metahuman assets for integration.  
- Visual checks are **checklists** (+ optional screenshot diffs later).  
- Performance tests extend `benchmarks/` and assert soft budgets from master §9.  
- Do not require Studio/Qt for unit tests.

### Suggested layout

```text
tests/
  avatar/
    test_manifest_loader.py
    test_mesh_loader.py
    test_skeleton_loader.py
    test_bind_pose.py
    test_skinning.py
    test_animation_runtime.py
    test_retarget.py
    test_validation.py
    test_avatar_runtime_integration.py
  test_benchmark_harness.py   # existing + Phase 1 benches
```

---

## 2. Asset loading

| Test | Type | Assert |
|------|------|--------|
| Manifest parsing (valid) | unit | fields present |
| Manifest invalid schema | unit | error diagnostic |
| Mesh loading NPZ/GLB | unit/integration | vertex count > 0 |
| Texture loading + missing fallback | unit | no throw; fallback used |
| Material loading / preset ID | unit | metallic/roughness set |
| Skeleton loading | unit | bone count, names unique |
| LOD selection | unit | quality → lod index |

---

## 3. Skeleton

| Test | Type | Assert |
|------|------|--------|
| Parent–child relationships | unit | tree matches fixture |
| Bone local→world FK | unit | known matrices |
| Bind pose correctness | unit | IBM @ world ≈ I |
| Coordinate system metadata | unit | up/forward parsed |
| Duplicate names rejected | unit | `SKEL_DUP_NAME` |
| Cycle rejected | unit | `SKEL_CYCLE` |

---

## 4. Skinning

| Test | Type | Assert |
|------|------|--------|
| Weight normalization | unit | sum == 1 |
| Influence clamp | unit | max K respected |
| Index OOB detection | unit | error |
| Single-bone 90° rotation | unit | vertex orbit exact |
| Deformation finite | integration | no NaN after 100 frames |

---

## 5. Animation

| Test | Type | Assert |
|------|------|--------|
| Clip loading | unit | duration > 0 |
| Playback advance | unit | time increases by dt * speed |
| Looping | unit | wraps |
| Speed control | unit | 2× advances twice as far |
| Interpolation / slerp | unit | midpoint quat unit length |

---

## 6. Retargeting

| Test | Type | Assert |
|------|------|--------|
| Joint mapping accuracy | unit | all map entries resolve |
| Pose conversion finite | unit | output pose OK |
| Scale consistency | unit | cm/m conversion |
| Rotation accuracy | unit | golden angles within ε |
| Missing joints → bind | unit | unmapped stay at rest |
| AXYX → avatar integration | integration | mesh bounds sane |

---

## 7. Runtime

| Test | Type | Assert |
|------|------|--------|
| Avatar switching | integration | procedural ↔ digital via AvatarManager |
| Frame updates | integration | update+render no throw (Null/offscreen) |
| Scene graph integration | integration | RenderNode present or documented draw path |
| Rendering lifecycle | integration | state machine READY during play |
| No viewer import from avatar | dependency | existing layering test still passes |

---

## 8. Performance

| Bench | Metric | Gate (initial) |
|-------|--------|----------------|
| Avatar load | ms | master §9 |
| Animation update | ms | ≤ 1 ms mean |
| Skinning | ms | ≤ 8 ms LOD1 |
| Frame time | ms | ≤ 16.7 ms offscreen path |
| Memory | KiB/MB | no growth > threshold over 1000 frames |

Implement in `benchmarks/harness.py`; CI runs reduced repeats; nightly full.

---

## 9. Visual validation (manual / semi-auto)

Checklist per milestone (attach screenshots in PR):

- [ ] Bind pose: avatar matches expected T/A pose  
- [ ] Single bone rotate: deformation localizes correctly  
- [ ] Native clip: motion plausible  
- [ ] Retarget walk/gait: feet/hips coherent  
- [ ] Switch procedural ↔ digital: camera/lighting unchanged  

Optional later: screenshot hash tests (out of scope for M1).

---

## 10. Regression

- Keep all Phase-0 / freeze tests green (`tests/test_rendering_*.py`, `test_architecture_freeze.py`, …).  
- Procedural metallic avatar remains default if digital load fails.  
- Public API imports (`motion_engine.api.*`) unchanged.

---

## 11. CI expectations

```text
pytest tests/ -q
python -m benchmarks.run_benchmarks --repeats 5
```

Avatar asset large binaries: use cached NPZ in repo or CI cache; document download step if needed.
