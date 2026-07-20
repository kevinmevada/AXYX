# AXYX rendering architecture benchmarks

CPU-side harness for architecture freeze + Milestone 1 asset pipeline.

```bash
# Architecture suite
python -m benchmarks.run_benchmarks
python -m benchmarks.run_benchmarks --repeats 30 --json bench.json

# Research-grade M1 asset pipeline (perf_counter_ns, cold/warm separated)
python -m benchmarks.m1_asset_pipeline --iterations 50
python -m benchmarks.m1_asset_pipeline --iterations 100 --out benchmarks/results

# Via pytest
pytest benchmarks/ tests/test_benchmark_harness.py tests/test_m1_benchmarks.py -q
```

## M1 outputs

Written under `benchmarks/results/`:

* `m1_asset_pipeline.md` — Markdown report
* `m1_asset_pipeline.csv` — flat metrics
* `m1_asset_pipeline.json` — full statistics

Timers use `time.perf_counter_ns()` only (never `time.time()`).
Cold and warm avatar loads are never averaged together.
Production loaders are not instrumented — all timing lives in `benchmarks/`.
