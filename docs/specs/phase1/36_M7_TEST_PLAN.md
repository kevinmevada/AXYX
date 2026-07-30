# 36 — M7 Test Plan

## System (`tests/system/`)

Lifecycle, session, manager, configuration, profiler, logging, statistics, cache, validation, resource cleanup, pipeline.

## Integration (`tests/integration/`)

Full runtime, motion→avatar, database (optional), animation, skinning, retarget, M1–M6 regression.

## Visual (`tests/visual/test_m7_system.py`)

Idle/walk/run/jump, mirror/root motion, avatar switching.

## Benchmarks

`benchmarks/m7_system.py` — cold/warm prepare, 1000 frames, memory, fps.

## Certification

`tests/certification/certify_phase1.py` — Phase 1 PASS/FAIL (includes M1–M6 cert subprocesses).

## Commands

```powershell
.\venv311\Scripts\Activate.ps1
python -m pytest tests/system tests/integration tests/visual/test_m7_system.py -q
python benchmarks/m7_system.py
python tests/certification/certify_phase1.py
python examples/minimal_pipeline.py
```
