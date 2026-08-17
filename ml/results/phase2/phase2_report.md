# Phase 2 Gait Feature Discovery Engine

Generated: 2026-08-13

Victimization labels were **not** used in feature construction or aggregation.
Default subject summary is the **median** across that subject's cycles.
Derivatives use Savitzky-Golay (window 11, poly 3) on the 101-point cycle; ROM/min/max do not.
Spatial axes are `ax1/ax2/ax3` until the lab coordinate convention is certified.

## Coverage

- Cycles: 880
- Subjects: 31
- Cycle-level feature columns: 714
- Subject-level columns: 3665 (each cycle feature × median/mean/std/cv/n, plus symmetry and variability)
- Catalog entries: 805
- Label columns leaked: none

Phase 3 should default to `*__median` subject columns unless a dispersion feature is the scientific target.

## Families (catalog)

- coordination: 8
- kinematic: 390
- phase: 240
- smoothness: 3
- spatial: 64
- symmetry: 58
- temporal: 9
- variability: 33

## Cycle-level QA

- Features with complete subject coverage: 714
- Features with some missingness: 0
- Features unavailable: 0

No victim-vs-control tests were run. That is Phase 3.

## Completion

- Kinematic, temporal, spatial, phase, coordination, smoothness at cycle level
- Symmetry (ipsilateral-aligned) and variability at subject level
- Feature catalog + anatomy metadata
- Cycle and subject parquet tables
- Feature quality table

