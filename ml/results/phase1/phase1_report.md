# Phase 1 Gait Event & Cycle Engine

Status: **PASS**

Generated: 2026-08-13

Read-only. `data/raw/` and `data/processed/` were not modified.
The processed MAT remains the canonical trajectory store.
Normalized core signals (0–100%, 101 points) are in `results/phase1/gait_cycles/normalized_core.npz`.

## Side encoding (empirically validated)

KinFC column 2 is a side code. Heel-Z at each contact (lower heel = contacting foot) across all 260 walking trials maps:

- code `1` → **R**
- code `2` → **L**

This was measured, not assumed. The user-facing example that treated `1` as left is therefore incorrect for this dataset.

## Dataset coverage

- Walking trials inspected: 260 (expected 260)
- Event validation PASS/WARNING/FAIL: 260/0/0
- Mapping mismatches vs heel vote: 0

## Cycles

- Total gait cycles (ipsilateral FC → next ipsilateral FC): 880
- Left: 440
- Right: 440
- PASS: 880
- PASS WITH WARNINGS: 0
- FAIL: 0
- Usable for lower-body analysis: 880
- Normalized 0–100% (101 points, all core signals): 880

## Subject-level usable cycles

- Victims (n=17): min 4, median 32.0, max 44, sum 487
- Controls (n=14): min 3, median 30.5, max 44, sum 393

### Victims

- S3: 8 trials, 28 usable cycles (L 14 / R 14)
- S4: 9 trials, 23 usable cycles (L 9 / R 14)
- S5: 8 trials, 15 usable cycles (L 7 / R 8)
- S7: 8 trials, 26 usable cycles (L 12 / R 14)
- S8: 9 trials, 30 usable cycles (L 16 / R 14)
- S13: 5 trials, 15 usable cycles (L 7 / R 8)
- S14: 8 trials, 32 usable cycles (L 15 / R 17)
- S15: 9 trials, 43 usable cycles (L 21 / R 22)
- S19: 4 trials, 4 usable cycles (L 3 / R 1)
- S26: 9 trials, 44 usable cycles (L 22 / R 22)
- S27: 10 trials, 36 usable cycles (L 21 / R 15)
- S31: 9 trials, 33 usable cycles (L 17 / R 16)
- S32: 11 trials, 16 usable cycles (L 9 / R 7)
- S34: 9 trials, 35 usable cycles (L 18 / R 17)
- S37: 9 trials, 37 usable cycles (L 17 / R 20)
- S38: 9 trials, 35 usable cycles (L 17 / R 18)
- S46: 9 trials, 35 usable cycles (L 17 / R 18)

### Controls

- S2: 9 trials, 37 usable cycles (L 18 / R 19)
- S9: 9 trials, 33 usable cycles (L 17 / R 16)
- S11: 9 trials, 23 usable cycles (L 10 / R 13)
- S12: 7 trials, 17 usable cycles (L 10 / R 7)
- S17: 9 trials, 41 usable cycles (L 20 / R 21)
- S23: 9 trials, 41 usable cycles (L 21 / R 20)
- S30: 5 trials, 3 usable cycles (L 1 / R 2)
- S35: 12 trials, 19 usable cycles (L 10 / R 9)
- S39: 10 trials, 44 usable cycles (L 22 / R 22)
- S40: 8 trials, 31 usable cycles (L 16 / R 15)
- S41: 8 trials, 24 usable cycles (L 12 / R 12)
- S42: 6 trials, 30 usable cycles (L 13 / R 17)
- S43: 6 trials, 17 usable cycles (L 10 / R 7)
- S48: 10 trials, 33 usable cycles (L 18 / R 15)

## Event irregularities

All walking trials have alternating KinFC sides after decoding.

## Quality policy

- Upper-arm gaps (LUPA/RUPA/RFRM) do **not** fail a cycle if lower-body coverage is intact.
- Missing opposite foot-contact or implausible duration (outside 0.50–2.20 s) fails the cycle.
- Missing FO, 0 or >2 mid-stance events, unusual duration (outside 0.70–1.60 s), or incomplete lower-body → PASS WITH WARNINGS, still usable for lower-body gait.
- Upper-body gaps (arms/head/trunk) are recorded per domain and do **not** change overall cycle status.

## Provenance

Each `cycle_id` encodes `Subject_Trial_Side_Index`, e.g. `S14_WU01_L_03`.
`start_frame` / `end_frame` are MATLAB 1-based KinFC frames for AXYS visualization.

## Core gait signals normalized

LASI, RASI, LPSI, RPSI, LHJC, RHJC, LHipAngles, RHipAngles, LKJC, RKJC, LKneeAngles, RKneeAngles, LAJC, RAJC, LAnkleAngles, RAnkleAngles, LAbsAnkleAngle, RAbsAnkleAngle, LHEE, RHEE, LTOE, RTOE, LFootProgressAngles, RFootProgressAngles, CentreOfMass, CentreOfMassFloor

## Completion criteria

- All walking trials inspected
- KinFC / KinFO / Midsvnt parsed
- Event side encoding validated against heel height
- Gait cycles extracted (left and right)
- Cycle durations calculated
- Invalid cycles identified
- Cycle quality scored by domain
- Subject- and trial-level cycle counts calculated
- Core gait signals assessed and normalized to 0–100% (101 points)
- Full provenance retained
- No source data modified

