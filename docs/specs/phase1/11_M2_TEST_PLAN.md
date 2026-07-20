# 11 — M2 Test Plan

**Milestone:** M2 Avatar Skeleton Runtime

---

## Unit tests (`tests/skeleton/`)

| File | Focus |
|------|-------|
| `test_bone.py` | Transform TRS, Bone properties/immutability |
| `test_hierarchy.py` | LCA, ancestors, path, depth, cycle helper |
| `test_lookup.py` | O(1) find/exists/parent/children |
| `test_traversal.py` | DFS/BFS/post/leaves determinism |
| `test_validation.py` | Malformed skeletons rejected |
| `test_statistics.py` | Counts and branching |
| `test_factory.py` | M1 → M2 conversion |
| `test_serialization.py` | JSON / tree export |
| `test_performance.py` | Lookup/validation sanity budgets |
| `test_regression.py` | M1 DTO freeze, no Studio/Viewer imports |

Run:

```bash
python -m pytest tests/skeleton -q
```

---

## Benchmarks

```bash
python -m benchmarks.m2_avatar_skeleton --iterations 100
```

Metrics: construction, validation, lookup, traversal, FK propagation,
serialization, statistics. Reports: min/max/mean/median/stdev/p95 via
`perf_counter_ns`.

---

## Certification

```bash
python tests/certification/certify_m2_avatar_skeleton.py
```

Exit `0` PASS / `1` FAIL.

Sections: hierarchy, lookup, traversal, validation, statistics, serialization,
performance, architecture, regression.
