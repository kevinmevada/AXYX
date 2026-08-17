# Phase 6 Time-Resolved Trajectory Analysis

Generated: 2026-08-13

## 1. Objective

Determine whether victimized and non-victimized females differ in **normalized gait trajectories** (0–100%, 101 points) after subject-level aggregation.

## 2. Motivation from Phases 3–5

Phase 3 found no FDR-supported summary-feature signature. Phase 4 found no victim-enriched phenotype. Phase 5 found no within-victim structure. Phase 6 tests whether **aggregation into scalars hid localized time-resolved differences**.

## 3. Dataset

880 Phase 1 normalized cycles; 31 subjects; 101 time points; 86 channels tested.

## 4. Independent unit

**n = 31 subjects.** Cycles are repeated measures. Inferential n is never 880.

## 5. Trajectory source

`results/phase1/gait_cycles/normalized_core.npz` (certified Phase 1). No renormalization.

## 6. Subject-level construction

Within-subject **nanmedian** across that subject's cycles (mean stored as sensitivity). No pooling across people.

## 7. Quality control

Channels require all 31 subjects to have ≥90% finite time points. Ineligible channels excluded (n=0). No silent zero-fill. No inferential interpolation.

## 8. Primary statistical method

Welch t-statistic time series; cluster-forming threshold |t|>2.045; cluster mass = sum |t| on contiguous suprathreshold points.

Primary channels (frozen): LHipAngles_ax1, RHipAngles_ax1, LKneeAngles_ax1, RKneeAngles_ax1, LAnkleAngles_ax1, RAnkleAngles_ax1, LFootProgressAngles_ax1, RFootProgressAngles_ax1, CentreOfMass_ax1, CentreOfMass_ax2, CentreOfMass_ax3

## 9. Permutation methodology

H0: no systematic victim/control trajectory difference. Permute **subject labels**; keep each 101-point trajectory intact. Primary permutations=9999; secondary=1999; seed=20260813. Never shuffle time or cycles.

## 10. Temporal correction

Cluster-based permutation (max cluster mass) controls the family of 101 time points within a channel.

## 11. Signal-level correction

Benjamini–Hochberg FDR within analysis level (primary / primary_asymmetry / secondary / secondary_asymmetry).

## 12. Shape analysis

Savitzky–Golay window 11, poly 3 (Phase 2). Peak/min timing and magnitude, n extrema, vel RMS. Mann–Whitney + BH.

none FDR≤0.10

## 13. Bilateral asymmetry

A(t)=L−R and |L−R| on hip, knee, ankle, foot-progression ax1 subject medians.

## 14. Subject consistency

Predefined: share of victims on the group-difference side of the **control median** at each time point.

## 15. Leave-one-out

Sign of the regional mean difference after dropping each subject.

## 16. Bootstrap

1000 within-group subject resamples; percentile CI for regional mean median-difference.

## 17. Candidate trajectory regions

ROBUST=0; EXPLORATORY=0. Strongest (lowest permutation p): RHipAngles_ax1 77.0-83.0% δ=0.42617046818727494 p=0.1469 q=0.1469 class=UNSUPPORTED

## 18. Marker/joint localization

See anatomy tables and `related_marker` on candidates. Axes remain ax1/ax2/ax3.

## 19. Cross-check against Phase 2/3

`source_phase` column: A already in Phase 3 FDR, B new/unmatched, C related but Phase 3 not FDR-significant.

## 20. Limitations

n=31; cluster threshold is conventional; secondary search is large; coordinate convention not certified as AP/ML/vertical.

## 21. Scientific conclusion

Outcome A: No robust time-resolved victim-associated gait difference was detected.

## 22. Recommendations for Phase 7

Do not train a victim classifier on these 31 people. If any exploratory region is pursued, preregister it on new subjects.

Phase 7 was not started.
