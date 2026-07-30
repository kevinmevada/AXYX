# 37 — System Certification

Phase 1 is certified when `certify_phase1.py` prints `Result: PASS`.

## Verified

- Asset loading / skeleton / bind pose
- Skinning / animation / retarget
- Unified runtime one-click pipeline
- Performance + memory snapshots
- M1–M6 regression certifications
- Architecture composition (no frozen API breaks)

## Final demonstration workflow

1. Construct `RuntimeFactory().debug()` or research preset  
2. `select_subject` / `select_trial` / `select_avatar`  
3. `prepare` → `play` / `run_frames`  
4. Clinical (or synthetic clinical) motion drives avatar  
5. Statistics + profiler available without manual wiring  
