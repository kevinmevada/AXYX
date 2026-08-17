# P0.6 Continuous relative phase (CRP) coordination

Generated: 2026-08-17

## Question

Do the 17 victims share *inter-joint coupling* (CRP profiles) that is invisible
to single-curve / single-feature tests (P0.1–P0.4)?

Unit: **subject** (n=31). Labels shuffled across subjects only.

## CRP method (audited)

- **Input:** Phase 1 `normalized_core.npz` ax1 angle curves (101 points).
- **Velocity:** not stored in Phase 1; not required for Hilbert phase.
- **Phase:** Hilbert analytic signal of the **demeaned** angle
  (`scipy.signal.hilbert` → `np.angle`).
- **Why Hilbert (not atan2(ω, θ)):** phase-plane methods need separate
  position/velocity normalization and are sensitive to those choices; Hilbert
  phase is unique for a demeaned real signal without an extra velocity scale
  (standard CRP practice in motor coordination).
- **CRP:** `wrap(φ_proximal − φ_distal)` to (−π, π].
- **Subject profile:** circular mean CRP across cycles.
- **Similarity:** (1) circular `mean_t cos(CRP_i−CRP_j)` — preserves constant
  phase offsets that z-scored Pearson would destroy; (2) DTW on
  `unwrap(CRP−CRP[0])` for time-varying coupling shape (P0.3-style).

Pairs locked in `preregistered_pairs.json` (n=6) before any real test.
FDR family = 12 (6 pairs × 2 measures).

## Pre-residual

| Metric | Circular mean cos(ΔCRP) (↑) | DTW on unwrap (↓) |
|---|---|---|
| Mean pairwise (avg over pairs) | 0.8374 | 16.6049 |
| 95% bootstrap CI | [0.8086, 0.8853] | [12.3493, 17.3494] |
| Permutation p | 0.5536 | 0.6883 |
| Null mean | 0.8395 | 16.0354 |
| LOSO pass / sign agree | True / 1.000 | — |
| Pairs with FDR q ≤ 0.10 | 0 | 0 |

## Post-residual (height, mass, mean leg length, cycle duration)

Linear residualization of wrapped CRP radians (pragmatic confound control).

| Metric | Circular mean cos(ΔCRP) (↑) | DTW on unwrap (↓) |
|---|---|---|
| Mean pairwise (avg over pairs) | 0.6494 | 17.6251 |
| 95% bootstrap CI | [0.6241, 0.7233] | [13.1688, 18.9195] |
| Permutation p | 0.929 | 0.6048 |
| Null mean | 0.6763 | 17.2248 |
| LOSO pass / sign agree | True / 1.000 | — |
| Pairs with FDR q ≤ 0.10 | 0 | 0 |
| Covariates | height_cm, mass_kg, mean_leg_cm, cycle_duration_s_median |

## Decision (P0.6 only)

**NULL after residualization**

Gate: post-residual primary. Needs perm p ≤ 0.05 on Pearson or DTW (with
Pearson LOSO pass), observed on the similarity side of the null, and ≥1
pair×measure FDR q ≤ 0.10.

Phases 0–6 were not modified. P1 not started in this script.
