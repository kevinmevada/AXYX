# 16 — M3 Test Plan

## Unit tests (`tests/pose/`)

| File | Focus |
|------|-------|
| `test_bind_pose.py` | Pose ABC, IBM, AnimationPose |
| `test_pose_factory.py` | Skeleton → bind, cache, kinds |
| `test_transform_propagation.py` | FK determinism |
| `test_matrix_utils.py` | Invert / quat / ortho |
| `test_validation.py` | Malformed poses |
| `test_statistics.py` | Counts / depth |
| `test_lookup.py` | O(1) accessors |
| `test_serialization.py` | JSON / report |
| `test_cache.py` | PoseCache |
| `test_regression.py` | M1/M2 freeze, no circular imports |

```bash
python -m pytest tests/pose -q
```

## Benchmarks

```bash
python -m benchmarks.m3_bind_pose --iterations 100
```

## Certification

```bash
python tests/certification/certify_m3_bind_pose.py
```
