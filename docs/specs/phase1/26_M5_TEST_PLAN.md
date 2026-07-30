# 26 — M5 Test Plan

| Suite | Path |
|-------|------|
| Unit | `tests/animation/` |
| Visual | `tests/visual/test_m5_animation_playback.py` |
| Certification | `tests/certification/certify_m5_animation_runtime.py` |
| Benchmarks | `benchmarks/m5_animation_runtime.py` |

## Coverage targets

- Keyframe / track / clip
- SLERP / looping / seek
- Player / controller / blending
- Events / markers / cache
- Serialization / regression
- M4 pose consumption

Run:

```bash
python -m pytest tests/animation tests/visual/test_m5_animation_playback.py -q
python tests/certification/certify_m5_animation_runtime.py
python benchmarks/m5_animation_runtime.py
```
