# P0.2 Shared abnormality-set overlap

Generated: 2026-08-16

## Question

Do the 17 victims share *which* preregistered features fall outside the control
10th–90th percentile band — a discrete abnormality set — even if continuous
deviation directions (P0.1) do not align?

Statistic: mean pairwise Jaccard among victim binary exceedance vectors.

Unit: **subject** (n=31). Labels shuffled across subjects only.

Feature list locked in `preregistered_features.json` **before** any real test
(n=30). No post-hoc search of the full Phase 2 matrix.

## Pre-residual (raw preregistered features)

| Metric | Value |
|---|---|
| Mean pairwise Jaccard (victims) | 0.1916 |
| 95% bootstrap CI | [0.1920, 0.3054] |
| Permutation p (greater) | 0.449 |
| Null mean / 95th pct | 0.1889 / 0.2466 |
| Mean victim exceedance prevalence | 0.282 |
| LOSO top-5 feature-rank agreement / pass | 0.742 / False |
| Features with co-exceedance FDR q ≤ 0.10 | 0 |

## Post-residual (height, mass, mean leg length, cycle duration)

Continuous features residualized on covariates **before** control-band
binarization.

| Metric | Value |
|---|---|
| Mean pairwise Jaccard (victims) | 0.1906 |
| 95% bootstrap CI | [0.2013, 0.2925] |
| Permutation p (greater) | 0.6032 |
| Null mean / 95th pct | 0.2012 / 0.2595 |
| Mean victim exceedance prevalence | 0.292 |
| LOSO top-5 feature-rank agreement / pass | 0.968 / False |
| Features with co-exceedance FDR q ≤ 0.10 | 0 |
| Covariates | height_cm, mass_kg, mean_leg_cm, cycle_duration_s_median |

## Decision (P0.2 only)

**NULL after residualization**

Gate: primary evidence is the **post-residual** result. A defensible shared-set
signal requires perm p ≤ 0.05, LOSO feature-rank pass, and observed Jaccard
above the permutation null mean after residualization.

Per-feature co-exceedance + BH-FDR is a diagnostic (fingerprint), not a second
primary claim.

Phases 0–6 were not modified. P0.3–P0.6 not run in this script.
