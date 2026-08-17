# P0-family synthesis — cross-cohort victim gait similarity

Generated: 2026-08-17

**Unit of analysis:** subject (n=31; 17 victimized / 14 control). Never cycles.  
**Phases 0–6:** frozen and untouched by this package.  
**Seed:** 20260813. Permutations: subject-label shuffles (≥9999 unless noted).

---

## Question the P0 battery asked

Do the 17 victimized women share a locomotor pattern *with each other* that
controls do not — a shared deviation direction, abnormality set, waveform shape,
phase-localized signature, or inter-joint coupling — that univariate mean
differences and whole-cohort classifiers would miss?

---

## Pre-registered tests and post-residual outcomes

| ID | Construct | Primary statistic (post-residual) | Null mean | Perm p | FDR survivors | LOSO | Gate |
|---|---|---|---|---|---|---|---|
| **P0.1** | Shared deviation *direction* (Phase 4 27-D) | mean pairwise cosine = **0.052** | 0.110 | **0.758** | — | pass | **NULL** |
| **P0.2** | Shared abnormality *set* (30 locked features) | mean pairwise Jaccard = **0.191** | 0.201 | **0.603** | 0/30 co-exceed | top-5 unstable | **NULL** |
| **P0.3** | Shared waveform *shape* (12 z-scored curves) | Pearson **−0.023** / DTW **7.657** | −0.030 / 7.591 | **0.267 / 0.629** | 0/12 | fail (near-zero) | **NULL** |
| **P0.4** | *Phase-localized* mean/ROM (5 event windows × 12 curves × 2 aggs × 2 tests) | FDR family **240** | — | min raw p=0.019 | **0 at q≤0.10** | window multivariate null | **NULL** |
| **P0.5** | Confound as shared residual pattern | *Not a separate discovery test* — height/mass/leg/cycle-duration residualization was applied as the primary gate in P0.1–P0.4 and P0.6 | — | — | — | — | **folded in** |
| **P0.6** | Shared inter-joint *CRP coupling* (6 Hilbert pairs) | circular sim **0.649** / DTW **17.63** | (perm null higher/similar) | **0.929 / 0.605** | **0/12** | — | **NULL** |

Every pre-registered discovery claim that survived confound residualization,
LOSO (where applicable), and BH-FDR was **null**.

---

## What each null means (and does not)

- **P0.1:** Victims are not aligned in a common direction away from the control centroid in family-PC space (obs cosine *below* null).
- **P0.2:** Victims do not share which locked features exceed the control 10–90% band more than chance.
- **P0.3:** After stripping amplitude, victim waveform shapes are not more alike than random groups of 17 (pre-residual Pearson looked high but matched the null — generic gait shape).
- **P0.4:** Restricting to event-derived phases (LR, MSt, TSt, PSw, undivided swing — ISw/MSw/TSw not reconstructable from stored events) does not reveal a localized shared signature under a 240-cell FDR family.
- **P0.6:** Hilbert CRP coupling on hip–knee, knee–ankle, hip–ankle (L/R) is not more similar among victims than among permuted groups. High absolute circular similarity (~0.65–0.84) is *shared gait coordination*, not victim-specific.

Taken together, these are complementary nulls: continuous direction, discrete exceedance, shape, phase window, and coupling were each tested on their own terms.

---

## Decision-gate recommendation

**Honest conclusion for this sample:** there is **no defensible shared victim
locomotor signature** under the P0 similarity program as pre-registered.
A P0.1 power simulation (empirical injection on the residualized 31-point
cloud; 1000 datasets × 999 perms) had **80% power only at λ ≥ 0.73**
(shared offset ≥ 0.73× typical control `||d||`; expected cosine ≈ 0.30).
The observed cosine 0.052 is far below that threshold.

**On P1 (Wasserstein / RV / soft-DTW / common subspace):**  
Given **six consecutive null decision gates** (P0.1–P0.4, P0.6; P0.5 absorbed
into residualization), starting P1 on the *same* 31-subject cohort would be
exploratory dredging unless there is a new, independently motivated hypothesis
and preferably an **external cohort**. The original gate’s spirit is: stop when
similarity discovery is exhausted and null — do not escalate metric complexity
to force a positive.

**Recommendation:** **Do not start P1 without explicit go-ahead.** Prefer
reporting the cumulative null and, if further work is desired, design it as
*confirmatory* on new data or a sharply constrained secondary question — not as
another open search on these 31 subjects.

---

## Deliverable map

| Path | Content |
|---|---|
| `results/similarity/p01_deviation/` | Cosine deviation alignment |
| `results/similarity/p02_abnormality/` | Jaccard abnormality sets |
| `results/similarity/p03_shape/` | Z-scored shape Pearson/DTW |
| `results/similarity/p04_event_phases/` | Event-window battery (240 FDR) |
| `results/similarity/p06_coordination/` | Hilbert CRP circular/DTW |
| `results/similarity/power_analysis/` | P0.1 MDE / power curve (post-hoc; does not alter frozen P0 tests) |
| `src/gait_research/similarity/` | Reusable package (deviation, abnormality, shape_space, event_phases, coordination_crp) |

---

## Explicit stop

P0 battery complete. **P1 code not started.** Await go-ahead before any
Wasserstein / RV / soft-DTW / common-subspace implementation.
