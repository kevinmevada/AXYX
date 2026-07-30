# 31 — M6 Test Plan

## Unit (`tests/retarget/`)

| Test | Coverage |
|------|----------|
| `test_mapping.py` | Builtin profiles, JSON roundtrip, resolve |
| `test_joint_mapping.py` | Primary map, one-to-many |
| `test_coordinate_mapper.py` | Identity + Z-up→Y-up |
| `test_rotation_mapper.py` | Unit quat, bind delta |
| `test_translation_mapper.py` | Scale, relative |
| `test_scale_mapper.py` | Height ratio |
| `test_root_motion.py` | World / in-place / loop |
| `test_constraints.py` | Soft clamp, hard fail |
| `test_offsets.py` | Offset table |
| `test_proportions.py` | Finite scales |
| `test_filters.py` | MA + all FilterKind |
| `test_validation.py` | Profile / pose / unit quats |
| `test_statistics.py` | Aggregator timing |
| `test_serialization.py` | Export profile/stats/meta |
| `test_cache.py` | Hits / clear |
| `test_regression.py` | Bind immutability, gait, mirror |

## Visual (`tests/visual/test_m6_retarget.py`)

Source/target overlay data, walking phases, mirroring, skinning consume, in-place root.

## Benchmarks

`benchmarks/m6_retarget.py` — 100 iterations, min/max/mean/median/stdev/p95 via `time.perf_counter_ns()`.

## Certification

`tests/certification/certify_m6_retarget.py` — PASS/FAIL.

## Commands

```powershell
.\venv311\Scripts\Activate.ps1
python -m pytest tests/retarget tests/visual/test_m6_retarget.py -q
python benchmarks/m6_retarget.py
python tests/certification/certify_m6_retarget.py
```
