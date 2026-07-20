# 03 — Bind Pose

**Parent:** [00_PHASE1_MASTER_SPEC.md](00_PHASE1_MASTER_SPEC.md)  
**Milestone:** M2  
**Code target:** `rendering/avatar/skeleton/bind_pose.py`, `inverse_bind_matrix.py`

---

## 1. Purpose

Bind pose is the reference configuration of the skeleton used when skin weights were authored. Incorrect bind pose → melted meshes. This doc is **critical path** for Phase 1.

---

## 2. Definitions

| Term | Meaning |
|------|---------|
| **Rest / bind local** | Bone transform relative to parent in bind pose |
| **Rest / bind world** | Bone transform in model space in bind pose |
| **Inverse bind matrix (IBM)** | `inverse(world_rest[bone])` — maps model-space points into bone space |
| **Skin matrix** | `world_pose[bone] @ IBM[bone]` — used per influence in skinning |

---

## 3. Inverse bind matrices

### Storage

- One 4×4 matrix per bone: `inverse_bind[i]`
- Float64 for authoring math; float32 acceptable for GPU upload later
- Row/column convention must match `transforms.py` and skinning kernel — **one convention, documented once**

### Sources (priority)

1. Explicit IBM from GLTF / skin accessor / NPZ cache  
2. Computed: `IBM[i] = inverse(world_rest[i])` from hierarchy + local rest  
3. If both present: prefer file IBM; validate against computed within epsilon

### Validation

```text
|| IBM_file[i] @ world_rest[i] - I || < ε   (e.g. 1e-3 relative)
```

Mismatch → warning or error based on magnitude.

---

## 4. Local transforms

Each bone stores bind-local TRS:

- Translation (parent space)  
- Rotation (unit quaternion)  
- Scale (default `(1,1,1)`)

Composition: `M = T @ R @ S` (document exact order; stay consistent with glTF: `T * R * S`).

---

## 5. Global transforms

```text
world_rest[root] = local_rest[root]
world_rest[i]    = world_rest[parent(i)] @ local_rest[i]
```

Implement iterative FK in bone order (parents before children).

---

## 6. Rest pose reconstruction

Given only IBMs (some pipelines):

```text
world_rest[i] ≈ inverse(IBM[i])
```

Recover local:

```text
local_rest[i] = inverse(world_rest[parent]) @ world_rest[i]
```

Root: `local_rest = world_rest`.

Round-trip test: reconstruct → recompute IBM → compare to original.

---

## 7. Coordinate conversion

If import bakes coordinates:

- Apply a single model-root transform `C` (coord conversion) to all world rests **or** to mesh + skeleton consistently.
- IBMs must be updated: `IBM' = IBM @ inverse(C)` or equivalent — **mesh and skeleton must share space**.

Prefer: keep avatar space in skeleton; convert only in retarget (`06`) for poses. Mesh vertices stay in avatar bind space matching IBM.

---

## 8. Scale handling

| Case | Policy |
|------|--------|
| Uniform scale on root | Allowed; track `model_scale` for retarget |
| Non-uniform bone scale in bind | Warning; skinning must include scale in matrices |
| Unit mismatch (cm vs m) | Manifest `units`; scale_mapper in retarget |
| Negative scale / reflections | Error — not supported in Phase 1 |

---

## 9. Validation checklist

- [ ] IBM count == bone count  
- [ ] IBM finite (no NaN/Inf)  
- [ ] `IBM @ world_rest ≈ I`  
- [ ] Quaternions normalized  
- [ ] Scales positive  
- [ ] Rest FK matches stored world if both provided  

Failures produce diagnostics codes (e.g. `BIND_IBM_MISMATCH`).

---

## 10. Public operations

```python
class BindPose:
    def compute_world_rest(self, skeleton) -> None: ...
    def compute_inverse_binds(self) -> None: ...
    def validate(self, eps: float = 1e-3) -> ValidationReport: ...
    def skin_matrix(self, bone_index: int, world_pose: Mat4) -> Mat4:
        return world_pose @ self.inverse_bind[bone_index]
```

---

## 11. Acceptance

- [ ] Rest pose reconstructed from hierarchy  
- [ ] IBMs present and validated  
- [ ] Round-trip IBM ↔ world_rest within tolerance  
- [ ] Unit tests for synthetic 2-bone and real avatar skeleton  
- [ ] Visual: mesh in bind pose matches T-pose / A-pose asset without animation  
