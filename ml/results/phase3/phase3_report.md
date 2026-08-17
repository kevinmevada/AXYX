# Phase 3 Statistical Gait Signature Discovery

Generated: 2026-08-13

Unit of analysis: **subject** (n=31; 17 victimized / 14 control). Cycles were never treated as independent samples.
Screening and redundancy used **no group labels**. Labels were joined only for group comparison.
No classifier, victim score, or accuracy claim was computed.

## Design

- Analysis columns: 805 (`*__median`, `var_*`, `sym_*`)
- Passed quality screen: 743
- Redundancy representatives (Spearman |ρ|≥0.90 clusters): 335
- Permutations: 999 subject-label shuffles, seed 20260813
- FDR: Benjamini–Hochberg on Mann–Whitney raw p-values

## Results

- FDR ≤ 0.05: 0
- FDR ≤ 0.10: 0
- Signature-rule features: 0

- Smallest Mann–Whitney raw p: 0.01104
- Smallest subject-permutation p: 0.008

No feature met the pre-specified signature rule (FDR ≤ 0.1, |Cliff's δ| ≥ 0.33, LOSO direction ≥ 0.80, victim consistency ≥ 0.60). The ranked list below is exploratory and must not be treated as a confirmed victim gait signature.

## Critical issues

- None for unit of analysis, label timing, FDR, effect sizes, or robustness **methods**. Those were implemented as specified.

## Warnings

- **No FDR-supported group difference.** After Benjamini–Hochberg on 335 representative tests, zero features have q ≤ 0.10 or q ≤ 0.05.
- Uncorrected permutation p-values can look small (some < 0.05) and must not be read as a signature. They are not multiplicity-controlled.
- n=17 vs n=14 has low power; a true medium effect can fail FDR.
- The exploratory top-20 list is a ranking aid for Phase 4/5, not confirmed victim-specific gait.

## Known limitations

- Subject is the unit; cycle-level pseudo-replication was avoided, which correctly reduces apparent power versus treating 880 cycles as independent.
- Spearman clustering can merge scientifically distinct but correlated metrics.
- Bootstrap CIs for Cliff's δ are subject-resampled, not cycle-resampled.
- Axes remain ax1/ax2/ax3.
- Phase 4 independent validation was not run.

## Pre-specified signature rule

- BH FDR q ≤ 0.10
- |Cliff's δ| ≥ 0.33 (medium)
- Leave-one-subject-out direction agreement ≥ 0.80
- Victim directional consistency ≥ 0.60 (share of victims on the group-difference side of the control median)

Ranking uses effect magnitude, FDR weight, LOSO stability, consistency, coverage, and family interpretability — not p-value alone.

## Ranked candidates (top 10 of exploratory/signature list)

| Rank | Feature | Direction | Cliff δ | FDR q | LOSO dir | Victim cons. | Region | Status |
|---:|---|---|---:|---:|---:|---:|---|---|
| 1 | `LHipAngles_ax3_tpeak_vel_pct__median` | VICTIMS_LOWER | -0.492 | 0.9961 | 1.00 | 0.88 | hip | exploratory |
| 2 | `LKneeAngles_ax3_tmax_pct__median` | VICTIMS_LOWER | -0.542 | 0.9961 | 1.00 | 0.76 | knee | exploratory |
| 3 | `RKneeAngles_ax3_peak_acc__median` | VICTIMS_HIGHER | 0.487 | 0.9961 | 1.00 | 0.82 | knee | exploratory |
| 4 | `LFootProgressAngles_ax2_mean__median` | VICTIMS_LOWER | -0.437 | 0.9961 | 1.00 | 0.88 | foot | exploratory |
| 5 | `LFootProgressAngles_ax1_std__median` | VICTIMS_LOWER | -0.412 | 0.9961 | 1.00 | 0.88 | foot | exploratory |
| 6 | `RAnkleAngles_ax3_peak_acc__median` | VICTIMS_HIGHER | 0.395 | 0.9961 | 1.00 | 0.88 | ankle | exploratory |
| 7 | `LHipAngles_ax2_tpeak_vel_pct__median` | VICTIMS_LOWER | -0.424 | 0.9961 | 1.00 | 0.76 | hip | exploratory |
| 8 | `LAnkleAngles_ax1_phase_40_50_rom__median` | VICTIMS_LOWER | -0.462 | 0.9961 | 1.00 | 0.76 | ankle | exploratory |
| 9 | `RFootProgressAngles_ax3_peak_acc__median` | VICTIMS_HIGHER | 0.412 | 0.9961 | 1.00 | 0.76 | foot | exploratory |
| 10 | `LKneeAngles_ax3_peak_acc__median` | VICTIMS_HIGHER | 0.353 | 0.9961 | 1.00 | 0.88 | knee | exploratory |

## Anatomical summary

| Region | Features | |δ|≥0.33 | FDR pass | max |δ| |
|---|---:|---:|---:|---:|
| knee | 80 | 8 | 0 | 0.542 |
| hip | 64 | 7 | 0 | 0.492 |
| ankle | 87 | 4 | 0 | 0.462 |
| foot | 66 | 5 | 0 | 0.437 |
| mixed | 21 | 1 | 0 | 0.395 |
| pelvis | 8 | 0 | 0 | 0.303 |
| whole_body | 2 | 0 | 0 | 0.277 |
| gait_cycle | 7 | 0 | 0 | 0.210 |

## Limitations

See Warnings and Known limitations above. Exploratory ranks are not a victim classifier.

Phase 4 (predictive ML) was not started.

