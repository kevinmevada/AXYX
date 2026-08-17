# P0.1 power / minimum-detectable effect

Generated: 2026-08-17

## Question

At n=17 victims vs 14 controls in residualized Phase 4 27-D space, how large
a **shared deviation direction** would P0.1 have been likely to detect?

This does not re-run or alter the frozen P0.1 test. It asks whether the
observed null (cosine 0.052, p=0.758) is unsurprising given the design's
sensitivity.

## Method

- **Noise model:** the frozen residualized 31 × 27 Phase 4 cloud itself.
  Each replicate randomly partitions those 31 points into 17/14 and, for
  λ>0, adds a shared offset of length `λ × median_control||d||` to the 17
  (same shared-direction generator as `test_deviation.test_shared_direction_detected`,
  with empirical residual noise instead of isotropic Gaussian).
  A parametric Ledoit–Wolf MVN fit to the 14 controls failed the null-shape
  check (too spherical; simulated λ=0 cosine mean 0.06 vs residualized
  permutation null 0.11) and was not used for the headline MDE.
- **Typical individual scale:** median **control** `||d_i||` = 8.3830.
- **Effect size λ:** shared offset Euclidean length = `λ × median ||d_control||`
  along a random unit direction (same generative pattern as
  `test_deviation.test_shared_direction_detected`, with real residual noise
  replacing isotropic N(0, 0.3²I)).
- **Test:** the actual P0.1 statistic (mean pairwise cosine among 17 labeled
  victims, one-sided subject-label permutation).
- **Simulations:** 1000 datasets per λ; 999 permutations
  per dataset (reduced from P0.1's 9999 for compute; documented). α = 0.05.
- **Seed:** 20260813.

## Sanity checks

| Check | Result |
|---|---|
| False-positive rate at λ=0 | 0.052 (target ~0.05) |
| Power at λ=3.0 | 1.000 (must approach 1) |
| Simulated λ=0 cosine mean vs real P0.1 null mean | 0.109 vs 0.110 (rel. diff 0.01) |
| Simulated λ=0 cosine SD vs real P0.1 null SD | 0.076 vs 0.077 (rel. diff 0.01) |

## Power curve

| λ | Power | Mean observed cosine | Rejections |
|---|---|---|---|
| 0.00 | 0.052 | 0.109 | 52/1000 |
| 0.25 | 0.091 | 0.140 | 91/1000 |
| 0.50 | 0.291 | 0.211 | 291/1000 |
| 0.75 | 0.848 | 0.308 | 848/1000 |
| 1.00 | 0.995 | 0.399 | 995/1000 |
| 1.25 | 1.000 | 0.475 | 1000/1000 |
| 1.50 | 1.000 | 0.547 | 1000/1000 |
| 2.00 | 1.000 | 0.653 | 1000/1000 |
| 3.00 | 1.000 | 0.789 | 1000/1000 |

## Headline MDE

**80% power at λ = 0.73** (shared-direction magnitude as a fraction of
typical individual control deviation). At that λ, simulated mean pairwise
cosine is approximately **0.300**.

This design had approximately **80% power to detect a shared deviation
direction of magnitude ≥ 0.73× the typical individual control
deviation-vector norm** (equivalently: a shared offset that produces mean
pairwise cosine among victims of about 0.300 under this noise model).
The observed residualized cosine (0.052) is **smaller than this detection threshold** (expected cosine at the 80% MDE ≈ 0.300) and is therefore consistent with being undetectable given n=17 vs 14. That MDE is a *large* shared shift: victims would need a common offset of 0.73× a typical control's entire residual deviation (median ||d|| = 8.38 in 27-D) before this n=17 vs 14 design reliably detects it. At λ=0.50, simulated power was only 29%. This battery is powered for a gross shared direction, not a subtle one.

Observed P0.1 residualized cosine = 0.052 (perm p = 0.758).

## What this does not say

- It does not turn the P0.1 null into a positive.
- It does not estimate power for P0.2–P0.6 (not run; P0.1 is the primary MDE).
- λ>0 is a shared Euclidean offset in a random direction on the empirical
  residual cloud — one alternative, not every possible shared pattern.
  If the λ=0 vs residualized-permutation-null gap is large, do not trust
  the MDE.

Phases 0–6 and P0.1–P0.6 result files were not modified.
