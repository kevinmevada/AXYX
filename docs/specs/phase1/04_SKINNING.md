# 04 — Skinning

**Parent:** [00_PHASE1_MASTER_SPEC.md](00_PHASE1_MASTER_SPEC.md)  
**Milestone:** M3  
**Code target:** `rendering/avatar/runtime/skinning_runtime.py`

---

## 1. Purpose

Deform mesh vertices from bind pose to animated pose using bone influences and weights. Phase 1 ships **correct CPU skinning**; GPU skinning is an interface stub only.

---

## 2. Vertex weights

Per vertex:

```text
joint_indices: int[K]    # bone indices
joint_weights: float[K]  # non-negative weights
```

Typical `K = 4` (glTF). Support `K ≤ 8` in data model; Phase 1 CPU path may clamp to 4 highest weights with renormalization.

---

## 3. Bone influences

Classic LBS (Linear Blend Skinning):

```text
v' = Σ_j w_j * (world_pose[j] @ IBM[j] @ v_bind)
n' = normalize( Σ_j w_j * (R_j @ n_bind) )   # rotation part only for normals
```

- Positions: full 4×4 skin matrices  
- Normals: inverse-transpose of upper 3×3 or rotation-only approximation (document choice; prefer correct inverse-transpose for non-uniform scale)

---

## 4. CPU skinning

`SkinningRuntime`:

```python
def apply(
    mesh: SkinnedMesh,
    skeleton: AvatarSkeleton,
    world_poses: Sequence[Mat4],
    *,
    out_positions: np.ndarray,
    out_normals: np.ndarray | None = None,
) -> None: ...
```

Requirements:

- Vectorized NumPy where practical  
- No per-frame heap alloc in steady state (reuse buffers / pose cache)  
- Metrics: `PerformanceMetrics.skinning_ms`

---

## 5. Future GPU skinning interface

```python
class SkinningBackend(Protocol):
    def upload_rest_mesh(self, mesh_id: str, mesh: SkinnedMesh) -> None: ...
    def set_bone_palette(self, matrices: np.ndarray) -> None: ...  # (B, 4, 4)
    def skin(self, mesh_id: str) -> None: ...
```

- Phase 1: `CpuSkinningBackend` only  
- `BackendCapabilities.supports_skinning` stays `False` on PyVista until GPU path lands  
- Do not block M3 on GPU

---

## 6. Weight normalization

On load:

```text
if sum(w) <= ε: assign full weight to root or first bone; warn
else: w = w / sum(w)
```

Optional: drop influences below `1e-4` then renormalize.

Negative weights → clamp to 0 + warn.

---

## 7. Validation

| Check | Severity |
|-------|----------|
| Index out of bone range | error |
| K == 0 on skinned mesh | error |
| Weights not finite | error |
| Sum ≈ 0 | error after repair attempt |
| Sum ≠ 1 before normalize | warning (normalize) |
| > max influences | warning (truncate) |

Single-bone rotation test: rotate one bone 90°; vertices with weight 1.0 on that bone must rotate about bind joint; others stay put.

---

## 8. Integration

```text
Retarget / Animation → world_poses[]
  → SkinningRuntime.apply
  → update mesh GPU buffers / PyVista polydata points
  → render
```

Procedural avatar does **not** require LBS (line/sphere geometry). Digital avatar must.

---

## 9. Acceptance for M3

- [ ] Weights normalized on load  
- [ ] CPU LBS produces finite positions  
- [ ] Single-bone rotation verified (unit + visual checklist)  
- [ ] Skinning time recorded in metrics  
- [ ] GPU protocol stub exists, unused  
