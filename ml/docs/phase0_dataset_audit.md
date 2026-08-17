# Phase 0 Dataset Audit

Status: **PASS WITH WARNINGS**

Generated: 2026-08-13

This audit is read-only. `data/raw/` and `data/processed/` were not modified.

## Dataset

- Processed file: `C:/Users/mevad/Desktop/AXYS ML/data/processed/Data_structure_all_subs.mat`
- Subjects: 31 (expected 31) — PASS
- Walking trials (WU*): 260 (expected 260) — PASS
- Valid walking trials: 242
- Sampling rate: 100 Hz — PASS

## Labels

- Join key: Excel `Subject No` ↔ MATLAB `S#` — PASS
- Victimized (Y): 17 (expected 17)
- Non-victimized (N): 14 (expected 14)
- Split check: PASS

| Subject | Subject No | Victimized | Join OK |
|---|---:|:---:|:---:|
| S2 | 2 | N | True |
| S3 | 3 | Y | True |
| S4 | 4 | Y | True |
| S5 | 5 | Y | True |
| S7 | 7 | Y | True |
| S8 | 8 | Y | True |
| S9 | 9 | N | True |
| S11 | 11 | N | True |
| S12 | 12 | N | True |
| S13 | 13 | Y | True |
| S14 | 14 | Y | True |
| S15 | 15 | Y | True |
| S17 | 17 | N | True |
| S19 | 19 | Y | True |
| S23 | 23 | N | True |
| S26 | 26 | Y | True |
| S27 | 27 | Y | True |
| S30 | 30 | N | True |
| S31 | 31 | Y | True |
| S32 | 32 | Y | True |
| S34 | 34 | Y | True |
| S35 | 35 | N | True |
| S37 | 37 | Y | True |
| S38 | 38 | Y | True |
| S39 | 39 | N | True |
| S40 | 40 | N | True |
| S41 | 41 | N | True |
| S42 | 42 | N | True |
| S43 | 43 | N | True |
| S46 | 46 | Y | True |
| S48 | 48 | N | True |

## Raw MAT

- File: `C:/Users/mevad/Desktop/AXYS ML/data/raw/Data_structure_all_subs.mat`
- Subjects: 43
- Present in raw but not processed: S6, S10, S18, S21, S22, S25, S29, S33, S36, S45, S47, S50

## Signals

- Markers: 37 (expected 37)
- Joint angles: 26 (expected 26)
- Joint centers: 6 (LHJC, RHJC, LKJC, RKJC, LAJC, RAJC)
- Whole-body COM: 2
- Segment COM: 15
- Walking kinematics expected: 86
- Modal observed count: 86 — PASS

## Events

- KinFC (foot contact): 260/260 walking trials — PASS
- KinFO (foot off): 260/260 walking trials — PASS
- Midsvnt (mid-stance): 260/260 walking trials — PASS

## Subject trial balance

- All subjects: min 4, median 9.0, max 12 (sum 260)
- Victimized: min 4, median 9.0, max 11 (sum 143)
- Non-victimized: min 5, median 9.0, max 12 (sum 117)

Gait-cycle min/median/max per subject is deferred to Phase 1/2.

### Victims

- S3: 8 trials
- S4: 9 trials
- S5: 8 trials
- S7: 8 trials
- S8: 9 trials
- S13: 5 trials
- S14: 8 trials
- S15: 9 trials
- S19: 4 trials
- S26: 9 trials
- S27: 10 trials
- S31: 9 trials
- S32: 11 trials
- S34: 9 trials
- S37: 9 trials
- S38: 9 trials
- S46: 9 trials

### Controls

- S2: 9 trials
- S9: 9 trials
- S11: 9 trials
- S12: 7 trials
- S17: 9 trials
- S23: 9 trials
- S30: 5 trials
- S35: 12 trials
- S39: 10 trials
- S40: 8 trials
- S41: 8 trials
- S42: 6 trials
- S43: 6 trials
- S48: 10 trials

## Irregularities

- Critical: 0
- Warnings: 74

### Critical issues

None

### Warnings

- `nan_values` S3.WU01: S3.WU01.LUPA finite_ratio=0.2596 missing=693
- `nan_values` S3.WU02: S3.WU02.LUPA finite_ratio=0.6923 missing=264
- `nan_values` S3.WU03: S3.WU03.LUPA finite_ratio=0.4111 missing=507
- `nan_values` S3.WU05: S3.WU05.LUPA finite_ratio=0.5418 missing=444
- `nan_values` S3.WU06: S3.WU06.RUPA finite_ratio=0.9893 missing=9
- `nan_values` S3.WU06: S3.WU06.LUPA finite_ratio=0.2500 missing=630
- `nan_values` S3.WU07: S3.WU07.LUPA finite_ratio=0.6781 missing=366
- `nan_values` S3.static: S3.static.LBHD finite_ratio=0.2700 missing=219
- `nan_values` S3.static: S3.static.RNeckAngles finite_ratio=0.2700 missing=219
- `nan_values` S3.static: S3.static.LNeckAngles finite_ratio=0.2700 missing=219
- `nan_values` S3.static: S3.static.RHeadAngles finite_ratio=0.2700 missing=219
- `nan_values` S3.static: S3.static.LHeadAngles finite_ratio=0.2700 missing=219
- `nan_values` S7.WU02: S7.WU02.LUPA finite_ratio=0.5686 missing=330
- `nan_values` S7.WU03: S7.WU03.LUPA finite_ratio=0.9030 missing=78
- `nan_values` S8.WU07: S8.WU07.RUPA finite_ratio=0.8419 missing=129
- `nan_values` S11.static: S11.static.C7 finite_ratio=0.3377 missing=153
- `nan_values` S11.static: S11.static.RNeckAngles finite_ratio=0.3377 missing=153
- `nan_values` S11.static: S11.static.LNeckAngles finite_ratio=0.3377 missing=153
- `nan_values` S11.static: S11.static.RSpineAngles finite_ratio=0.3377 missing=153
- `nan_values` S11.static: S11.static.LSpineAngles finite_ratio=0.3377 missing=153
- `nan_values` S11.static: S11.static.LShoulderAngles finite_ratio=0.3377 missing=153
- `nan_values` S11.static: S11.static.LElbowAngles finite_ratio=0.3377 missing=153
- `nan_values` S11.static: S11.static.LWristAngles finite_ratio=0.3377 missing=153
- `nan_values` S11.static: S11.static.RShoulderAngles finite_ratio=0.3377 missing=153
- `nan_values` S11.static: S11.static.RElbowAngles finite_ratio=0.3377 missing=153
- `nan_values` S11.static: S11.static.RWristAngles finite_ratio=0.3377 missing=153
- `nan_values` S11.static: S11.static.RThoraxAngles finite_ratio=0.3377 missing=153
- `nan_values` S11.static: S11.static.LThoraxAngles finite_ratio=0.3377 missing=153
- `nan_values` S12.WK04Copy: S12.WK04Copy.LTHI finite_ratio=0.9885 missing=9
- `nan_values` S12.WK04Copy: S12.WK04Copy.LHipAngles finite_ratio=0.9885 missing=9
- `nan_values` S12.WK04Copy: S12.WK04Copy.LKneeAngles finite_ratio=0.9466 missing=42
- `nan_values` S12.WK04Copy: S12.WK04Copy.LAbsAnkleAngle finite_ratio=0.9466 missing=42
- `nan_values` S12.WK04Copy: S12.WK04Copy.LAnkleAngles finite_ratio=0.9466 missing=42
- `nan_values` S12.WK04Copy: S12.WK04Copy.LFootProgressAngles finite_ratio=0.9466 missing=42
- `nan_values` S12.WK04Copy: S12.WK04Copy.LKJC finite_ratio=0.9885 missing=9
- `nan_values` S12.WK04Copy: S12.WK04Copy.LAJC finite_ratio=0.9466 missing=42
- `nan_values` S12.WK04Copy: S12.WK04Copy.LeftFemurCOM finite_ratio=0.9885 missing=9
- `nan_values` S12.WK04Copy: S12.WK04Copy.LeftTibiaCOM finite_ratio=0.9466 missing=42
- `nan_values` S12.WK04Copy: S12.WK04Copy.LeftFootCOM finite_ratio=0.9466 missing=42
- `nan_values` S12.WK04Copy: S12.WK04Copy.CentreOfMass finite_ratio=0.9466 missing=42
- `nan_values` S12.WK04Copy: S12.WK04Copy.CentreOfMassFloor finite_ratio=0.9466 missing=42
- `nan_values` S12.staticCopy: S12.staticCopy.LSHO finite_ratio=0.1400 missing=258
- `nan_values` S12.staticCopy: S12.staticCopy.LUPA finite_ratio=0.0600 missing=282
- `nan_values` S12.staticCopy: S12.staticCopy.LShoulderAngles finite_ratio=0.1400 missing=258
- `nan_values` S12.staticCopy: S12.staticCopy.LElbowAngles finite_ratio=0.1400 missing=258
- `nan_values` S12.staticCopy: S12.staticCopy.LWristAngles finite_ratio=0.1400 missing=258
- `irregular_session_names` S12: S12 non-canonical session names: WK01Copy, WK02Copy, WK04Copy, WK05Copy, WK06Copy, WK07Copy, WK08Copy, WK09Copy, WK10Copy, WK11Copy, WU01Copy, WU02Copy, WU03Copy, WU04Copy, WU05Copy, WU07Copy, WU08Copy, staticCopy
- `nan_values` S14.WU01: S14.WU01.LKneeAngles finite_ratio=0.9368 missing=54
- `nan_values` S14.WU01: S14.WU01.LAbsAnkleAngle finite_ratio=0.9368 missing=54
- `nan_values` S14.WU01: S14.WU01.LAnkleAngles finite_ratio=0.9368 missing=54
- `nan_values` S14.WU01: S14.WU01.LFootProgressAngles finite_ratio=0.9368 missing=54
- `nan_values` S14.WU01: S14.WU01.CentreOfMass finite_ratio=0.9368 missing=54
- `nan_values` S14.WU01: S14.WU01.CentreOfMassFloor finite_ratio=0.9368 missing=54
- `nan_values` S14.WU01: S14.WU01.LAJC finite_ratio=0.9368 missing=54
- `nan_values` S14.WU01: S14.WU01.LeftTibiaCOM finite_ratio=0.9368 missing=54
- `nan_values` S14.WU01: S14.WU01.LeftFootCOM finite_ratio=0.9368 missing=54
- `irregular_session_names` S17: S17 non-canonical session names: WU0, WU3, WU4, WU5, WU6, WU7, WU9
- `nan_values` S19.WU03: S19.WU03.RFRM finite_ratio=0.2188 missing=525
- `missing_markers` S30.WU02: S30.WU02 missing markers ['LUPA']
- `unexpected_signal_count` S30.WU02: S30.WU02 has 85 kinematics fields, expected 86
- `missing_markers` S30.WU05: S30.WU05 missing markers ['LUPA']
- `unexpected_signal_count` S30.WU05: S30.WU05 has 85 kinematics fields, expected 86
- `missing_markers` S30.WU06: S30.WU06 missing markers ['LUPA']
- `unexpected_signal_count` S30.WU06: S30.WU06 has 85 kinematics fields, expected 86
- `missing_markers` S30.WU07: S30.WU07 missing markers ['LUPA']
- `unexpected_signal_count` S30.WU07: S30.WU07 has 85 kinematics fields, expected 86
- `nan_values` S32.WU03: S32.WU03.LFIN finite_ratio=0.9831 missing=9
- `nan_values` S32.WU03: S32.WU03.LWristAngles finite_ratio=0.9831 missing=9
- `nan_values` S32.WU03: S32.WU03.CentreOfMass finite_ratio=0.9831 missing=9
- `nan_values` S32.WU03: S32.WU03.CentreOfMassFloor finite_ratio=0.9831 missing=9
- `nan_values` S32.WU03: S32.WU03.LeftHandCOM finite_ratio=0.9831 missing=9
- `nan_values` S40.WU04: S40.WU04.LUPA finite_ratio=0.9892 missing=9
- `nan_values` S43.WU02: S43.WU02.RUPA finite_ratio=0.9706 missing=21
- `trial_imbalance` dataset: Walking trials per subject range 4–12 (median 9.0)

## Checks

- subject_count: PASS
- label_split: PASS
- join: PASS
- sampling_rate: PASS
- walking_trials: PASS
- walking_signal_count: PASS
- events_KinFC: PASS
- events_KinFO: PASS
- events_Midsvnt: PASS
- raw_mat_present: PASS
- survey_excel_present: PASS
- survey_table_present: PASS

## Completion criteria

- Processed MAT verified
- Raw MAT verified
- Survey Excel verified
- Subject ↔ survey join verified
- Walking trials inventoried
- Kinematic signals inventoried
- Marker / joint-angle / joint-center inventories verified
- Gait events verified
- Sampling rates verified
- Trajectory dimensions verified
- Missing values quantified
- Irregular sessions identified (not renamed)
- Subject trial balance reported
- No source data modified

