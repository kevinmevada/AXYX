# AXYX Phase 1 — Milestone 1 Final Audit & Freeze Report

**Date:** 2026-07-20  
**Scope:** Asset pipeline only (bind/rest pose load)  
**Constraint:** No feature work; no public API / Viewer / Studio / Rendering changes  

---

## Verdict

# M1 APPROVED FOR FREEZE

Functional correctness, architectural boundaries, and certification/regression evidence are sufficient to freeze Milestone 1.

Measured performance characteristics (especially ~4 s material/texture binding and warm≈cold) are **explained by design + asset choices**, not by broken timers or architecture violations. Optimizations are **deferred** (see Technical Debt).

---

## SECTION 1 — Benchmark Validation

### What each timer measures

| Metric | Measures | Overlap risk |
|--------|----------|--------------|
| `manifest_path_resolution` | `resolve_manifest_path` only | None |
| `manifest_parse` | `read_text` + `json.loads` only | None |
| `manifest_validation` | `ManifestValidator.validate` on already-parsed dict | None |
| `manifest_load_total` | Full `ManifestLoader.load` (resolve+parse+validate+build) | **Superset** of the three above — not intended to equal their sum |
| `mesh_file_read` / `mesh_decode` / extract / bounds | Isolated micro-ops on NPZ | Micro-ops are **not** a partition of `mesh_load_total` (handler does more: normals, joints, MeshData ctor copies) |
| `mesh_load_total` | Full `NpzMeshHandler.load` | Authoritative mesh timing |
| `skeleton_*` | Hierarchy JSON / NPZ bone tables / matrix copy / full load | Sub-metrics are alternate paths, not additive children of `skeleton_load_total` |
| `texture_disk_io` / `texture_decode` | PNG path read vs full `TextureLoader.load_file` | Decode includes I/O + PIL + float32 convert |
| `material_creation` | Procedural **preset** materials only (no image I/O) | Correctly isolated from binding |
| `material_texture_binding` | Metahuman `MaterialLoader.load_from_manifest` (includes all texture loads) | **Includes** texture decode — by design of that metric name |
| `avatar_stage_*` | Sequential stages inside one construction pass | **Additive:** stage sum ≈ `avatar_construction_total` (delta ≈ orchestration overhead only) |
| `cold_avatar_load` / `warm_avatar_load` | Full `AvatarLoader.load` | Measured **separately**; never averaged |

### Parent ≈ child (where intended)

From saved `benchmarks/results/m1_asset_pipeline.json` (means):

- Avatar staged sum ≈ construction total (delta small — expected).
- Manifest/mesh micro-sums **must not** equal totals (documented: micros are partial / overlapping probes).

**Conclusion:** Timers measure the intended operations. The only important semantic note is that **`material_texture_binding` includes texture decoding** (not pure MaterialData construction). Labels are accurate if read that way.

---

## SECTION 2 — Warm Cache Verification

### Evidence (staged `AvatarLoader` on metahuman)

| Stage | Call 1 | Call 2 (same process) |
|-------|--------|------------------------|
| Manifest | ~1.5 ms | ~1.1 ms |
| Mesh | ~3.9 ms | ~2.2 ms |
| Materials+textures | ~3314 ms | ~3645 ms |
| Skeleton | ~3.6 ms | ~3.1 ms |

Second-pass texture decode (same `TextureLoader` instance) still ~0.4–1.5 s **per** large map.

### Findings

`AvatarLoader.load()` **always**:

1. Re-parses the manifest  
2. Reloads mesh from disk/NPZ  
3. Re-decodes **every** material texture (no loader cache)  
4. Reloads skeleton  
5. Re-validates  

There is **no application-level warm cache** for textures or meshes. “Warm” in the benchmark suite only benefits from **OS page cache**, which does **not** avoid PIL decode or float32 conversion.

**Therefore warm ≈ cold is expected and correct**, not a timer bug.

---

## SECTION 3 — Texture Pipeline Audit (~4 s binding)

### Manifest paths actually loaded

| Slot | Manifest path | On disk | Resolution loaded |
|------|---------------|---------|-------------------|
| base_color | `T_Body_BC_VT.TGA` | 50 MB | **4096×4096** |
| normal | `T_Body_N_VT.TGA` | 201 MB | **8192×8192** |
| srmf | `T_Body_SRMF_VT.TGA` | 268 MB | **8192×8192** |
| scatter | `T_Body_Scatter_VT.TGA` | 0.8 MB | 512×512 |

Cached PNGs under `cache/textures/` (2048²) exist but are **not used**, because TGA files exist and `load_relative` only falls back to PNG when TGA is missing.

### Per-slot decode cost (measured)

| Slot | Time | float32 RGBA footprint |
|------|------|-------------------------|
| base_color TGA 4K | ~400 ms | ~268 MB |
| normal TGA 8K | ~1500 ms | ~1074 MB |
| srmf TGA 8K | ~1400 ms | ~1074 MB |
| scatter | ~44 ms | ~4 MB |
| **Sum** | **~3.3–3.5 s** | **~2.4 GB** |

### Root cause (evidence-backed)

1. **Image decoding** of source TGAs (dominant)  
2. **Conversion to float32 RGBA** + copy in `TextureImage.__post_init__`  
3. **Repeated decoding** on every `AvatarLoader.load` / material bind (no cache)  
4. File I/O is secondary once pages are warm  

**Not** a mysterious cache miss in the registry; registry cache hits are sub-microsecond when used.

### Recommendations (deferred — do **not** change in M1 freeze)

1. Prefer `cache/textures/*.png` (2K) in `avatar.json` for runtime loads; keep TGA as source assets.  
2. Add optional `TextureLoader` memoization by resolved path (M1.1 / M2).  
3. Store uint8 textures until GPU upload (defer float32).  

---

## SECTION 4 — Memory Audit

| Observation | Evidence |
|-------------|----------|
| ~2.3 GiB LoadedAvatar “array footprint” | Sum of decoded float32 texture buffers (matches 4K+8K+8K math) |
| Mesh copy on construct | `MeshData.__post_init__` copies arrays (immutability) — small vs textures |
| Texture double-touch | PIL array + `TextureImage` copy |
| No Studio/Viewer leak path | Avatar package does not import Studio/Viewer |
| Duplicate loads | Every `load()` allocates new texture buffers (by design today) |

**Leaks:** No evidence of unbounded growth across a single load. Repeated loads **intentionally** re-allocate (no shared cache).

**Immutable sharing:** Models are frozen, but loaders do not yet share instances across loads — debt, not a correctness defect.

---

## SECTION 5 — Architecture Audit

| Check | Result |
|-------|--------|
| Circular imports | Package import order succeeds |
| Viewer/Studio imports in avatar pipeline | **0** violations (AST scan) |
| Dependency direction | loaders → models; registry → loader; validation → models/loader exceptions |
| SOLID | SRP per loader; OCP via `MeshFormatHandler`; DIP via injected loaders |
| Frozen public APIs | `motion_engine.api.*` surface intact; Viewer/Studio untouched |
| Duplicated responsibilities | Legacy soft `avatar_manifest` facade coexists with strict `ManifestLoader` — acceptable compat shim |

---

## SECTION 6 — Code Quality Tooling

| Tool | Status in this environment |
|------|----------------------------|
| ruff | **Not installed** in `venv311` |
| mypy | **Not installed** |
| black | **Not installed** |

Quality gates that **did** run:

- `tests/avatar/test_asset_pipeline_m1.py`  
- `tests/test_m1_benchmarks.py`  
- Architecture freeze + dependency rules + rendering architecture + renderer tests  

**Recommendation (process, not M1 code):** add ruff/mypy/black to CI in a later hygiene milestone. Absence of those tools here is an environment gap, not an M1 functional failure.

---

## SECTION 7 — Regression

Executed successfully:

```text
53 passed  (avatar M1 + m1 benchmarks + architecture freeze + dependency rules
            + rendering architecture + renderer)
```

Prior full certification run: **Overall PASS** (all 13 sections), including research-grade performance section.

---

## Strengths

1. Clear loader SRP and immutable `LoadedAvatar` contract  
2. Data-driven manifests + stable asset IDs  
3. GLB/GLTF + NPZ extensibility without public API churn  
4. Validation + structured exceptions  
5. Research-grade benchmarks with cold/warm separation and export artifacts  
6. Certification harness as an engineering gate  

---

## Remaining technical debt (accepted for freeze)

| ID | Debt | Severity | Target |
|----|------|----------|--------|
| TD-1 | Manifest points at 4K/8K TGA instead of 2K PNG cache | Perf | M1.1 asset tweak |
| TD-2 | No texture/mesh memoization in loaders → warm≈cold | Perf | M2+ |
| TD-3 | float32 full-res decode for CPU path | Memory/perf | When GPU path lands |
| TD-4 | `TextureImage` copies buffers again | Memory | Minor |
| TD-5 | Lint/type tools not in current venv/CI | Process | Hygiene milestone |
| TD-6 | Benchmark micro-metrics are probes, not additive partitions | Docs | Keep documented |

---

## Recommended future optimizations (explicitly deferred)

1. Switch metahuman runtime material paths to `cache/textures/*.png`.  
2. Path-keyed texture cache inside `TextureLoader` (invalidate on hot-reload).  
3. Optional uint8 storage until present.  
4. Do **not** reinterpret warm≈cold as a benchmark defect without an app-level cache.

---

## Freeze statement

Milestone 1 (Research-Grade Asset Pipeline) is **frozen**:

- Behavior and public APIs for M1 loaders/models/registry/validation are baseline.  
- Further work proceeds as **M2+** (bind-pose depth, skinning, retarget) or documented M1.1 perf tweaks behind explicit approval.  
- No silent architecture or Viewer/Studio changes.

**Signed-off by audit:** M1 APPROVED FOR FREEZE
