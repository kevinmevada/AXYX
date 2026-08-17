# Phase 2 certification

Status: **PASS**

Generated: 2026-08-13

## Counts

- cycle_rows: 880
- cycle_feature_columns: 714
- subject_rows: 31
- subject_columns: 3665
- catalog_entries: 805
- cycle_specs: 714
- subject_extra_specs: 91
- expected_subject_columns: 3665

## Checks

- `no_label_leakage_tables`: **PASS** — cycle=none; subject=none
- `no_labels_in_feature_calculation`: **PASS** — no victimization tokens in features/ or aggregation/
- `catalog_labels_used_false`: **PASS** — catalog.labels_used=False
- `no_silent_imputation`: **PASS** — ROM uses finite-only drop; derivative path interpolates NaNs and is documented in the catalog
- `anatomical_metadata`: **PASS** — all specs have region/side/related_anatomy
- `units_allowed`: **PASS** — all units in controlled vocabulary
- `units_inherited_flagged`: **PASS** — no inherited placeholder units
- `source_signal_valid`: **PASS** — all source_signal values resolve to core signals, events, or cycle features
- `axes_not_anatomical`: **PASS** — feature names/descriptions use ax1/ax2/ax3, not AP/ML/vertical
- `catalog_coordinate_note`: **PASS** — AP/ML/vertical not certified; spatial features use axis_1/2/3.
- `cycle_catalog_vs_table`: **PASS** — catalog 714 vs table 714; only_catalog=[]; only_table=[]
- `catalog_805_reconcile`: **PASS** — all_specs=805 cycle=714 extra=91 (expected extra symmetry+variability)
- `subject_columns_traced`: **PASS** — subject_cols=3665 expected=3665 untraced=none
- `savitzky_golay_documented`: **PASS** — window=11 poly=3 constants=11/3
- `phase_bins_0_100`: **PASS** — bins=((0, 10), (10, 20), (20, 30), (30, 40), (40, 50), (50, 60), (60, 70), (70, 80), (80, 90), (90, 100)); missing_names=none; ramp 0-10 mean=4.5 (expect 4.5); 90-100 mean=95.0 (expect 95)
- `within_subject_median_mean_sd_cv`: **PASS** — S14 LKneeAngles_ax1_rom median=65.71893581748009 vs recomputed 65.71893581748009
- `no_cross_subject_influence`: **PASS** — S3 LKneeAngles_ax1_rom median with all subjects=68.31004357337952; after dropping S2 cycles=68.31004357337952
- `symmetry_ipsilateral_pairing`: **PASS** — S14 |L-cycle LKnee - R-cycle RKnee|=6.620949447154999; stored=6.620949447154999; same-window-all-cycles |L-R|=7.183148235082626 (must not be the stored value unless equal)
- `deterministic_extract`: **PASS** — repeat kinematic extract identical

