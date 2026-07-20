# 09 — Acceptance Criteria

**Parent:** [00_PHASE1_MASTER_SPEC.md](00_PHASE1_MASTER_SPEC.md)  
**Rule:** Phase 1 is complete **only when every box below is checked** and evidence is linked (PR, test log, or benchmark JSON).

---

## 1. Pipeline & assets

- [ ] Avatar manifest loads (`avatar.json` via asset ID)
- [ ] Mesh loads (at least one LOD)
- [ ] Skeleton imports
- [ ] Bone hierarchy validated
- [ ] Bind pose reconstructed
- [ ] Inverse bind matrices validated
- [ ] Textures assigned (or documented fallback)
- [ ] Materials assigned
- [ ] Asset pack layout is self-contained under `assets/avatars/<name>/`

## 2. Animation & skinning

- [ ] Native animation plays (clip soak)
- [ ] Single bone rotation verified (automated + visual)
- [ ] Skinning verified (CPU LBS)
- [ ] Weight normalization / influence limits enforced

## 3. Retarget & clinical drive

- [ ] Canonical AXYX skeleton imported / referenced
- [ ] Joint mapping complete (data-driven map file)
- [ ] Coordinate conversion validated
- [ ] Scale conversion validated
- [ ] Runtime animation driven by AXYX poses
- [ ] Missing joints handled without NaNs / mesh explosion

## 4. Integration constraints (non-negotiable)

- [ ] Procedural and digital avatars switch at runtime (`AvatarManager`)
- [ ] **No Viewer changes required** (public viewer API stable)
- [ ] **No Studio changes required** (no Qt edits required for Phase 1 feature)
- [ ] Dependency rules still pass (`tests/test_dependency_rules.py`)
- [ ] Architecture freeze public APIs still importable

## 5. Quality gates

- [ ] All tests pass (`08_TEST_PLAN.md` matrix covered)
- [ ] Benchmarks collected (load, update, skin, frame, memory)
- [ ] Documentation updated (`docs/architecture/rendering.md` + this pack current)
- [ ] Validation report runs on metahuman + procedural packs in CI
- [ ] Performance targets met or explicitly waived with rationale in master amendment

## 6. Deliverable inventory

- [ ] `rendering/avatar/loader/` modules present
- [ ] `rendering/avatar/skeleton/` modules present
- [ ] `rendering/avatar/animation/` modules present
- [ ] `rendering/avatar/runtime/` modules present
- [ ] `rendering/avatar/retarget/` modules present
- [ ] `rendering/avatar/validation/` modules present
- [ ] Digital `Avatar` subclass registered via plugin / AvatarManager
- [ ] `docs/specs/phase1/` remains the contract (no silent drift)

---

## Sign-off

| Role | Name | Date | Notes |
|------|------|------|-------|
| Implementer | | | |
| Reviewer | | | |
| Architecture | | | Freeze still holds |

**Phase 1 complete:** ☐ Yes — proceed to clinical / Digital Twin product milestones  
**Not complete:** ☐ — list open items against checklist above  

---

## Evidence template

```text
PR: #
pytest: N passed
benchmarks: path/to/bench.json
screenshots: path/to/visual/
waivers: (none | link to master amendment)
```
