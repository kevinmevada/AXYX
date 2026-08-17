# P0.4 Event-localized phase-window similarity

Generated: 2026-08-17

## Question

Is victim similarity localized to specific clinical gait phases that whole-cycle
tests (P0.1–P0.3) dilute into noise?

Unit: **subject** (n=31). Labels shuffled across subjects only.

## Phase audit (pre-registration)

Phase 1 stores IC, opposite FO, mid-stance (Midsvnt), opposite FC, ipsilateral
FO, and next IC for all 880 cycles (100% complete; strict order).

**Reconstructable (used):** loading response, mid-stance, terminal stance,
pre-swing, undivided swing (5 windows).

**Not reconstructable (not estimated):** initial / mid / terminal swing splits
(no feet-adjacent, tibia-vertical, or equivalent events).

Locked in `preregistered_phases.json` before any real test.

## FDR family (stated before running)

**n = 240** = 5 phases × 12 P0.3 curves × 2 aggregations (mean, rom) × 2
tests (deviation cosine, abnormality Jaccard). BH-FDR spans this entire family
(not per-window).

## Pre-residual

| Metric | Value |
|---|---|
| FDR family size | 240 |
| Cells with FDR q ≤ 0.10 | 0 |
| Cells with FDR q ≤ 0.05 | 0 |
| Min raw perm p | 0.0279 |

## Post-residual (height, mass, mean leg length, cycle duration)

| Metric | Value |
|---|---|
| FDR family size | 240 |
| Cells with FDR q ≤ 0.10 | 0 |
| Cells with FDR q ≤ 0.05 | 0 |
| Min raw perm p | 0.0188 |
| Covariates | height_cm, mass_kg, mean_leg_cm, cycle_duration_s_median |

### Per-window multivariate (24-D: 12 curves × mean/rom) — LOSO

| Phase | Cosine | Cos p | Cos LOSO | Jaccard | Jac p | Jac LOSO |
|---|---|---|---|---|---|---|
| loading_response | -0.0369 | 0.9297 | False | 0.1474 | 0.8805 | False |
| mid_stance | -0.0491 | 0.9585 | True | 0.1494 | 0.7795 | False |
| terminal_stance | -0.0588 | 0.9987 | True | 0.1549 | 0.8945 | False |
| pre_swing | -0.0395 | 0.8476 | True | 0.1870 | 0.5443 | False |
| swing | -0.0523 | 0.968 | True | 0.1526 | 0.7953 | False |

## Decision (P0.4 only)

**NULL after residualization**

Gate: primary evidence is **post-residual** FDR across the full 240-cell
family. A defensible phase-localized claim requires ≥1 cell with FDR q ≤ 0.10
after residualization (and supporting window-level LOSO for that phase).

Phases 0–6 were not modified.

## Note on P0.5 / P0.6

P0.5 in the original plan (“confound as shared residual pattern”) is largely
already folded into P0.1–P0.4 via pre/post residualization on height/mass/leg/
cycle duration. Unless you want a dedicated residual-*pattern* similarity test
(victims share the confound-residual direction itself), the natural next step
after P0.4 is **P0.6 CRP/coordination**. Confirm or correct before proceeding.
