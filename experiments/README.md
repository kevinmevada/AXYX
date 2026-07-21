# Experiments

Place research trial scripts, ablations, and notes here.

## Skinning Debug Studio (M4 visual validation)

```bash
python -m experiments.skinning_debug.run --fixture
python -m experiments.skinning_debug.run --lod 3
```

See `experiments/skinning_debug/README.md`.

## Layout

```
experiments/
  skinning_debug/
    README.md
    run.py
    app.py
  2026-07-skeleton-fit/
    notes.md
    run.py
```

Generated artifacts should go under `results/`.
