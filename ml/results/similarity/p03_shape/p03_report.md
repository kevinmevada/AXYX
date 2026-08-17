# P0.3 Shared waveform shape (amplitude-normalized)

Generated: 2026-08-16

## Question

Do the 17 victims share *waveform shape / timing* on core gait curves after
discarding ROM/amplitude — a question neither P0.1 (PC-space direction) nor
P0.2 (binary exceedance) tested?

Unit: **subject** (n=31). Labels shuffled across subjects only.

## Amplitude normalization (preregistered)

**Z-score each subject-median curve across the 101 phase points** (zero mean,
unit variance), independently per curve. This explicitly discards amplitude/ROM
and DC offset; only shape/timing remains. The same z-scored curves enter both
Pearson and DTW so DTW cannot re-introduce magnitude.

Curve list locked in `preregistered_curves.json` **before** any real test
(n=12). Phase 1 core has pelvis *markers* (LASI/RASI), not
PelvisAngles — documented in the lock file.

## Pre-residual

| Metric | Pearson (↑ similar) | DTW distance (↓ similar) |
|---|---|---|
| Mean pairwise (victims, avg over curves) | 0.5524 | 4.0376 |
| 95% bootstrap CI | [0.5099, 0.7005] | [3.1591, 4.2377] |
| Permutation p | 0.4936 (greater) | 0.4902 (less) |
| Null mean / tail | 0.5533 / p95=0.5973 | 4.0312 / p05=3.7599 |
| LOSO sign agreement / pass | 1.000 / True | (distance; see LOSO range in tables) |
| Curves with FDR q ≤ 0.10 | 0 | 0 |

## Post-residual (height, mass, mean leg length, cycle duration)

Each (curve × phase %) column residualized across subjects **before** z-scoring
and similarity. Covariates: height_cm, mass_kg, mean_leg_cm, cycle_duration_s_median.

### Cycle duration × DTW (explicit flag)

Residualizing cycle duration removes linear associations between absolute gait
speed and the *value* of each phase-% sample. DTW on 0–100% normalized curves
already allows **nonlinear phase warping** of shape. These are different timing
constructs; neither replaces the other. Both Pearson and DTW are reported after
the same residualization — we do not silently drop duration for the DTW path.

| Metric | Pearson (↑ similar) | DTW distance (↓ similar) |
|---|---|---|
| Mean pairwise (victims, avg over curves) | -0.0234 | 7.6570 |
| 95% bootstrap CI | [-0.0439, 0.2584] | [5.9529, 7.7332] |
| Permutation p | 0.2669 (greater) | 0.6288 (less) |
| Null mean / tail | -0.0296 / p95=0.0178 | 7.5907 / p05=7.3056 |
| LOSO sign agreement / pass | 0.871 / False | — |
| Curves with FDR q ≤ 0.10 | 0 | 0 |

## Decision (P0.3 only)

**NULL after residualization**

Gate: primary evidence is **post-residual**. A defensible shared-shape claim
requires at least one of Pearson or DTW with perm p ≤ 0.05 and observed on the
similarity side of the null mean (Pearson above; DTW below), with Pearson also
requiring LOSO pass. The two measures are never averaged into one number.

Phases 0–6 were not modified. P0.4–P0.6 not run in this script.
