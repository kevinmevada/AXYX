# 06 — Retarget Engine

**Parent:** [00_PHASE1_MASTER_SPEC.md](00_PHASE1_MASTER_SPEC.md)  
**Milestone:** M5  
**Code target:** `rendering/avatar/retarget/`

---

## 1. Purpose

The **heart of Phase 1**: convert an AXYX canonical skeleton pose into an avatar skeleton pose so clinical mocap drives digital humans without rewriting Viewer/Studio.

```text
AXYX Pose (canonical)
    → JointMapper
    → CoordinateMapper
    → ScaleMapper
    → RotationMapper
    → PoseMapper
Avatar local/world pose
```

---

## 2. Canonical AXYX skeleton

Source of truth:

- `config/skeleton_definition.yaml`  
- `motion_engine.skeleton` / `SkeletonDefinition`  
- Procedural 15-point clinical set (and any extended definition used by mocap)

Retarget **inputs** are AXYX joint positions and/or local rotations in AXYX space (as provided by viewer frame / animation clip). Document the exact `Pose` / frame type accepted (`ProceduralPoseFrame`, `motion_engine.skeleton.Pose`, or a new neutral `CanonicalPose` DTO).

**Recommendation:** Introduce a small `CanonicalPose` dataclass in retarget (joint name → TRS or position) so avatar code does not import Studio types.

---

## 3. Avatar skeleton

Target: `AvatarSkeleton` from `02` (e.g. MetaHuman bone set). Many avatar bones will have **no** direct AXYX source — handled by missing-joint policy (§8).

---

## 4. Joint mapping

`joint_mapper.py` + data file (e.g. `assets/avatars/metahuman/skeleton/joint_map.json`):

```json
{
  "schema_version": "1.0.0",
  "canonical_to_avatar": {
    "Pelvis": "pelvis",
    "LHip": "thigh_l",
    "LKnee": "calf_l",
    "LAnkle": "foot_l"
  },
  "aliases": {
    "LeftUpLeg": "thigh_l"
  },
  "ignore_avatar_bones": ["ik_*", "weapon_*"]
}
```

Rules:

- One canonical → at most one primary avatar bone (Phase 1).  
- Unmapped canonical joints: skip with warning.  
- Unmapped avatar bones: missing-joint handling (§8).  
- Mapping is data — **no hardcoded name tables in Python** beyond test fixtures.

---

## 5. Coordinate conversion

`coordinate_mapper.py`:

- Read avatar `coordinate_system` from manifest vs AXYX (`config/coordinate_system.yaml`).  
- Build fixed change-of-basis matrix `C` (and inverse).  
- Apply to positions / rotation frames consistently.

Test: axis unit vectors map as documented (e.g. Unreal forward → AXYX forward).

---

## 6. Scale conversion

`scale_mapper.py`:

- Unit scale (cm↔m) from manifests  
- Optional **body scale**: match avatar pelvis–head height to subject height from mocap bounding box  
- Phase 1 minimum: unit conversion + single uniform `avatar_scale` from bind pose  

Hip height ratio method is acceptable for M5; full anthropometric calibration can be Phase 1.1.

---

## 7. Rotation conversion

`rotation_mapper.py`:

- Convert canonical joint orientations into avatar local rotations.  
- Strategies (pick one primary, document):
  1. **Look-at / swing** from parent→child position chains (works with position-only mocap)  
  2. **Direct quaternion map** when mocap provides orientations  
- Preserve twist heuristics for knees/elbows (hinge axis) — specify defaults; refine with tests.

T-pose / A-pose reference offsets: store `rest_delta` quaternions so bind orientations are accounted for.

---

## 8. Missing joint handling

| Situation | Policy |
|-----------|--------|
| Avatar bone with no canonical source | Hold **bind local** rotation/translation |
| Spine extras (spine_02…) | Optional copy from nearest mapped parent or bind |
| Fingers / face | Bind pose (Phase 1) |
| IK helpers / twist bones | Bind or procedural twist extraction (optional) |

Never leave NaNs. Never skip FK update for missing bones — use bind local.

---

## 9. Pose mapper (orchestration)

`pose_mapper.py` / `RetargetEngine`:

```python
class RetargetEngine:
    def __init__(self, joint_map, canonical_skel, avatar_skel, coord, scale): ...
    def map(self, canonical_pose: CanonicalPose) -> Pose: ...
    def validate(self) -> ValidationReport: ...
```

Output pose feeds `AnimationRuntime` / skinning (§05 / §04).

---

## 10. Validation

- Every mapped pair: both names resolve  
- Coordinate matrix determinant ≈ ±1 (warn if not rotation-like after scale extract)  
- After map: all avatar locals finite; world FK finite  
- Foot contact heuristic optional warning (not blocking)  
- Golden pose tests: known AXYX T-pose → avatar within angular/position epsilon  

---

## 11. Acceptance for M5

- [ ] Joint map loads from avatar pack (not hardcoded)  
- [ ] Coordinate conversion validated with unit tests  
- [ ] Scale conversion validated  
- [ ] Runtime animation driven by AXYX pose on digital avatar  
- [ ] Unmapped bones stay in bind without exploding mesh  
- [ ] Procedural path still works unchanged  

---

## 12. Non-goals

- Full HumanIK / MotionBuilder quality  
- Online learning of maps  
- Facial retarget  
