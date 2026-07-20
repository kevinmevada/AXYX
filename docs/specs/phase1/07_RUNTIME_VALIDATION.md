# 07 — Runtime Validation

**Parent:** [00_PHASE1_MASTER_SPEC.md](00_PHASE1_MASTER_SPEC.md)  
**Milestones:** M1–M7 (continuous)  
**Code target:** `rendering/avatar/validation/`

---

## 1. Purpose

Automatically detect asset and runtime problems **before** they become silent visual corruption. Validation never crashes Studio; it returns structured reports and raises only when callers use strict APIs.

---

## 2. Modules

| File | Role |
|------|------|
| `validator.py` | Orchestrates checks (asset + runtime) |
| `diagnostics.py` | Individual check functions + codes |
| `report.py` | `ValidationReport`, severities, serialization |

---

## 3. Severity

| Level | Meaning | Default host behavior |
|-------|---------|------------------------|
| `info` | FYI | Log debug |
| `warning` | Degraded but runnable | Log warning; continue |
| `error` | Unsafe to skin/render digital avatar | Fail `load()` in strict mode; fallback to procedural if policy says so |

---

## 4. Required detections

### Assets / manifest

| Check | Code (example) |
|-------|----------------|
| Missing / invalid manifest | `MANIFEST_INVALID` |
| Missing required mesh file | `MESH_MISSING` |
| Missing texture (optional) | `TEXTURE_MISSING` |
| Invalid / unsupported format | `FORMAT_UNSUPPORTED` |
| Schema version mismatch | `MANIFEST_SCHEMA` |

### Skeleton

| Check | Code |
|-------|------|
| Missing bones (empty) | `SKEL_EMPTY` |
| Duplicate bone names | `SKEL_DUP_NAME` |
| Broken hierarchy / bad parent | `SKEL_BAD_PARENT` |
| Cycles | `SKEL_CYCLE` |
| Unreachable bones | `SKEL_ORPHAN` |

### Bind pose

| Check | Code |
|-------|------|
| Missing IBM | `BIND_IBM_MISSING` |
| IBM mismatch vs world rest | `BIND_IBM_MISMATCH` |
| Non-uniform scaling | `BIND_NONUNIFORM_SCALE` |
| Non-finite transforms | `BIND_NONFINITE` |

### Skinning

| Check | Code |
|-------|------|
| Invalid weights / indices | `SKIN_WEIGHT_INVALID` |
| Influence out of range | `SKIN_INDEX_OOB` |
| Unnormalized weights (pre-fix) | `SKIN_WEIGHT_SUM` |

### Retarget

| Check | Code |
|-------|------|
| Map references unknown bone | `RETARGET_UNKNOWN_BONE` |
| Empty joint map | `RETARGET_MAP_EMPTY` |

### Runtime (per session / sampled frames)

| Check | Code |
|-------|------|
| Non-finite skinned positions | `RUNTIME_NONFINITE_MESH` |
| Pose buffer size mismatch | `RUNTIME_POSE_SIZE` |
| Avatar switch while loading | `RUNTIME_STATE` |

---

## 5. Report format

```python
@dataclass
class Diagnostic:
    code: str
    severity: Literal["info", "warning", "error"]
    message: str
    path: str | None = None  # asset path or bone name

@dataclass
class ValidationReport:
    ok: bool                 # False if any error
    diagnostics: list[Diagnostic]
    def to_dict(self) -> dict: ...
```

Logging: structured via logger; optional dump to JSON for CI.

---

## 6. When to run

| Phase | Trigger |
|-------|---------|
| Load | End of `AvatarLoader.load` |
| Bind | After IBM compute |
| Retarget init | After joint map resolve |
| Runtime | Debug flag / every N frames / on avatar switch |
| CI | Full asset pack validation job |

---

## 7. Policies

- **Strict load** (tests, CI): errors raise `AvatarLoadError` with report attached.  
- **Studio load**: errors → log + keep previous avatar or procedural fallback; never hard-crash Qt.  
- Duplicate detection must be deterministic (sorted codes in reports for golden tests).

---

## 8. Acceptance

- [ ] All checks in §4 implemented or explicitly deferred with ticket note in report  
- [ ] Unit tests feed broken fixtures (dup names, bad weights, missing texture)  
- [ ] Report serializes to JSON  
- [ ] Integration: bad metahuman pack fails CI validation test  
