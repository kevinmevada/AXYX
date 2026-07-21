# 21 — M4 Test Plan

```bash
python -m pytest tests/skinning tests/visual -q
python -m benchmarks.m4_skinning --iterations 100
python tests/certification/certify_m4_skinning.py
```

Unit: weights, normalization, validation, palette, runtime, CPU skinner,
vertex transform, deformer, statistics, serialization, regression.

Visual: bind, raised arm, bent elbow, spine proxy, walking oscillation.
