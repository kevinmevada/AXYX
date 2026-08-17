# P0.1 Deviation-direction alignment

Generated: 2026-08-16

## Question

Do the 17 victims share a common *direction* of deviation from the control
centroid in Phase 4's 27-D family-PC gait space?

Statistic: mean pairwise cosine among victim deviation vectors
`d_i = x_i − mean(controls)`.

Unit: **subject** (n=31). Labels shuffled across subjects only.

## Pre-residual (raw Phase 4 representation)

| Metric | Value |
|---|---|
| Mean pairwise cosine (victims) | 0.0640 |
| 95% bootstrap CI | [0.0163, 0.2754] |
| Permutation p (greater) | 0.9164 |
| Null mean / 95th pct | 0.1895 / 0.3652 |
| Mean cosine → victim-mean direction | 0.2339 |
| Consistency (frac cosines > 0) | 0.941 |
| LOSO sign agreement / pass | 1.000 / True |
| Frac victims above null mean | 0.118 |

## Post-residual (height, mass, mean leg length, cycle duration)

| Metric | Value |
|---|---|
| Mean pairwise cosine (victims) | 0.0518 |
| 95% bootstrap CI | [0.0018, 0.2513] |
| Permutation p (greater) | 0.7579 |
| Null mean / 95th pct | 0.1103 / 0.2566 |
| Mean cosine → victim-mean direction | 0.3099 |
| Consistency (frac cosines > 0) | 0.882 |
| LOSO sign agreement / pass | 1.000 / True |
| Covariates | height_cm, mass_kg, mean_leg_cm, cycle_duration_s_median |

## Decision (P0.1 only)

**NULL after residualization**

Gate: primary evidence is the **post-residual** result. A defensible shared-direction
signal requires perm p ≤ 0.05, LOSO pass, and bootstrap CI excluding ≤0 after residualization.

Phases 0–6 were not modified. P0.2–P0.6 not run in this script.
