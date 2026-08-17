# AXYS processed dataset blueprint

Female-only gait kinematics joined to victimization survey labels.

- Working file: `data/processed/Data_structure_all_subs.mat` (83.3 MB, MATLAB v7)
- Originals: `data/raw/`
- Date compiled: 13 August 2026

---

## 1. Snapshot

| Metric | Value |
|---|---|
| Subjects | 31 females |
| Label split | 17 victimized (Y) / 14 not (N) |
| Walking trials (WU*) | 260 |
| Kinematic sample rate | 100 Hz |
| Force-plate rate (recorded, traces not stored) | 1000 Hz |
| Trial duration | ~1.17–4.60 s (117–460 frames) |
| Foot contacts per trial | 2–8 |
| Mass | 47.7–100 kg (mean 64.1) |
| Height | 141–168 cm (mean 160.0) |

**What changed from raw**

- 12 male subjects removed.
- Survey columns from `Victimization surveys.xlsx` attached to each remaining subject.
- Join key: Excel `Subject No` = MATLAB `S{n}` (example: 14 → `Dat.S14`).
- Cohort-level `Dat.Res` dropped (it mixed sexes). Per-subject gait `Res` remains.

---

## 2. Files

| Role | Path | Contents |
|---|---|---|
| Raw MAT | `data/raw/Data_structure_all_subs.mat` | 43 subjects (31 F + 12 M), 111 MB |
| Raw survey | `data/raw/Victimization surveys.xlsx` | Subjects 1–50; sex, victimization, type, times, cyber |
| Processed MAT | `data/processed/Data_structure_all_subs.mat` | 31 females + Survey table; labels on each `Sn` |

**Join rule**

Use Excel column **Subject No**, not column **No**.

- `Subject No` is the lab ID and matches `Dat.S{n}`.
- `No` is only a 1–31 female roster index (`Survey.RosterNo`).

---

## 3. Survey field map

| Excel column | MATLAB field | Meaning |
|---|---|---|
| No | `Survey.RosterNo` | Female roster 1–31 |
| Subject No | `Survey.SubjectNo` | Lab ID; matches `Sn` |
| SEX | `Survey.Sex` | Always `F` in processed file |
| VICTIMIZED | `Survey.Victimized` | `Y` or `N` — primary ML label |
| person/online/both/ND/NO | `Survey.VictimType` | `Ip`, `online`, `Both`, `Nd`, or `No` |
| How many times | `Survey.Times` | Count or `Nd`; `0` if not victimized |
| CYBER BULLIED | `Survey.CyberBullied` | `Yes`, `No`, or `Nd` |

**Victim type among Y = 17:** Nd 7, in-person (Ip) 6, Both 3, online 1.

**CyberBullied overall:** Yes 6, Nd 6, No 19 (No includes all 14 non-victims).

---

## 4. Top-level MATLAB layout

One variable: `Dat`.

```
Dat
├── S2, S3, S4, S5, S7, S8, S9, S11, S12, S13, S14, S15, S17,
│   S19, S23, S26, S27, S30, S31, S32, S34, S35, S37, S38, S39,
│   S40, S41, S42, S43, S46, S48          (31 subjects)
└── Survey                                 (31-row table of all labels)
```

IDs not in the processed file: 1, 6, 10, 16, 18, 20–22, 24, 25, 28, 29, 33, 36, 44, 45, 47, 49, 50  
(males, empty survey rows, or “DO NOT USE”).

`Dat.Survey` is a MATLAB table (opens in MATLAB). SciPy cannot decode that table or MATLAB string objects.

---

## 5. Per-subject tree

Every subject has three branches: `Info`, `Survey`, `New_Session`.

```
Dat.S{n}
├── Info                         anthropometrics / capture settings
│   ├── FirstFrame, LastFrame
│   ├── Vrate = 100 Hz
│   ├── FPrate = 1000 Hz
│   ├── Mass (kg), Height (cm)
│   ├── LLegLength, RLegLength (cm)
│   └── RefThPosture, RefHdPosture   (MATLAB tables)
│
├── Survey                       joined Excel row
│   ├── RosterNo
│   ├── SubjectNo
│   ├── Sex
│   ├── Victimized
│   ├── VictimType
│   ├── Times
│   └── CyberBullied
│
└── New_Session
    ├── WU*                      walking trials (count varies, typically 4–12)
    │   ├── kinematics           86 signals, each (n_frames × 3)
    │   ├── Info                 gait events
    │   │   ├── KinFC            foot contact  [frame, side]
    │   │   ├── KinFO            foot off
    │   │   └── Midsvnt          mid-stance
    │   └── Res                  trial gait metrics (MATLAB tables)
    ├── static                   quiet-standing calibration
    ├── Res                      subject-level summary metrics
    └── RawRes                   unaggregated trial metrics
```

**Event arrays (`KinFC`, `KinFO`, `Midsvnt`):** size `k × 2`. Column 1 = frame index. Column 2 = side (`1` or `2`, left/right). Example S2 WU01 `KinFC`:

```
15 1
71 2
127 1
183 2
236 1
291 2
```

---

## 6. Kinematics dictionary

Walking trials: **86** trajectories. Static trials: **63** (markers + angles only; no joint centers or COMs).

Units: marker/COM coordinates in **millimetres**; joint angles in **degrees** (Plug-in Gait: flexion/extension, abduction/adduction, rotation).

### Markers (37)

| Group | Names |
|---|---|
| Head | LFHD RFHD LBHD RBHD |
| Trunk | C7 T10 CLAV STRN RBAK |
| Left arm | LSHO LUPA LELB LFRM LWRA LWRB LFIN |
| Right arm | RSHO RUPA RELB RFRM RWRA RWRB RFIN |
| Pelvis | LASI RASI LPSI RPSI |
| Left leg/foot | LTHI LKNE LANK LHEE LTOE |
| Right leg/foot | RTHI RKNE RANK RHEE RTOE |

### Joint angles (26)

| Group | Names |
|---|---|
| Lower limb | L/R Hip, Knee, Ankle, AbsAnkle; FootProgress |
| Pelvis / trunk | L/R Pelvis, Spine, Thorax |
| Head / neck | L/R Neck, Head |
| Upper limb | L/R Shoulder, Elbow, Wrist |

Full angle field names: `LHipAngles`, `LKneeAngles`, `LAbsAnkleAngle`, `LAnkleAngles`, `RHipAngles`, `RKneeAngles`, `RAnkleAngles`, `RAbsAnkleAngle`, `LPelvisAngles`, `RPelvisAngles`, `LFootProgressAngles`, `RFootProgressAngles`, `RNeckAngles`, `LNeckAngles`, `RSpineAngles`, `LSpineAngles`, `LShoulderAngles`, `LElbowAngles`, `LWristAngles`, `RShoulderAngles`, `RElbowAngles`, `RWristAngles`, `RThoraxAngles`, `LThoraxAngles`, `RHeadAngles`, `LHeadAngles`.

### Joint centers and COM (23) — walking trials only

| Group | Names |
|---|---|
| Joints | LHJC RHJC LKJC RKJC LAJC RAJC |
| Whole body | CentreOfMass, CentreOfMassFloor |
| Segments | PelvisCOM, Left/Right Femur Tibia Foot, ThoraxCOM, HeadCOM, Left/Right Humerus Radius Hand |

---

## 7. Precomputed gait metrics

Stored as MATLAB `table` objects. Readable in MATLAB; not numeric arrays in SciPy.

### Trial `Res`

| Field | Likely meaning |
|---|---|
| StpLen | Step length |
| StpWth | Step width |
| WkVel | Walking velocity |
| MTC | Minimum toe clearance |
| FCKneeAtt | Knee attitude at foot contact |
| MSKneeAtt | Knee attitude at mid-stance |
| MxStKneeAtt | Max stance knee attitude |
| Upright / nUpright | Trunk uprightness (raw / normalized) |
| NeckAng | Neck angle |

### Subject `Res` / `RawRes` extras

| Field | Where |
|---|---|
| KneeAtt | Subject Res (collapsed) |
| Cadence | Subject Res and RawRes |
| Smooth / Smoothi | Subject Res (smoothness) |
| Coord | Subject Res (coordination) |
| FC/MS/MxStKneeAtt | RawRes (per trial) |

---

## 8. Subject roster

Join labels to gait with **S#** (Subject No). Roster is the Excel `No` column.

| Roster | S# | Vic | Type | Times | Cyber | Mass kg | Ht cm | WU trials | Frames | FC | Notes |
|---:|---|:---:|---|---:|---|---:|---:|---:|---|---|---|
| 1 | S2 | N | No | 0 | No | 85.9 | 162.6 | 9 | 303–446 | 5–7 | |
| 2 | S3 | Y | Nd | 2 | Nd | 47.7 | 162.6 | 8 | 280–379 | 5–7 | WU11 instead of WU08 |
| 3 | S4 | Y | Both | 4 | No | 53.6 | 162.6 | 9 | 220–291 | 4–5 | WU10 not WU09 |
| 4 | S5 | Y | Nd | 2 | No | 52.7 | 167.6 | 8 | 214–270 | 3–5 | no WU06 |
| 5 | S7 | Y | Nd | 3 | Nd | 59.5 | 161.3 | 8 | 217–318 | 3–7 | no WU08 |
| 6 | S8 | Y | Ip | 3 | No | 85.5 | 163.8 | 9 | 253–330 | 4–6 | |
| 7 | S9 | N | No | 0 | No | 64.5 | 165.1 | 9 | 268–353 | 5–7 | |
| 8 | S11 | N | No | 0 | No | 70.9 | 161.3 | 9 | 204–290 | 4–5 | |
| 9 | S12 | N | No | 0 | No | 68.9 | 152.4 | 7 | 146–316 | 3–5 | WU*Copy + extra WK*Copy; staticCopy |
| 10 | S13 | Y | Nd | 4 | Nd | 100.0 | 165.1 | 5 | 262–320 | 5–5 | fewest WU trials |
| 11 | S14 | Y | Both | 12 | Yes | 54.5 | 160.0 | 8 | 209–383 | 5–7 | no WU02; max times=12 |
| 12 | S15 | Y | Both | 10 | Yes | 64.1 | 141.0 | 9 | 302–384 | 6–8 | shortest stature |
| 13 | S17 | N | No | 0 | No | 60.5 | 157.5 | 9 | 300–375 | 6–7 | WU0, WU3–WU7, WU9, WU11, WU13 |
| 14 | S19 | Y | Ip | Nd | Yes | 73.6 | 162.6 | 4 | 168–224 | 2–4 | fewest WU; no WU01 |
| 15 | S23 | N | No | 0 | No | 53.6 | 158.8 | 9 | 297–370 | 6–7 | |
| 16 | S26 | Y | Nd | Nd | Yes | 71.4 | 162.6 | 9 | 293–460 | 5–8 | longest trial 4.60 s |
| 17 | S27 | Y | Ip | 2 | Nd | 51.8 | 157.5 | 10 | 253–349 | 4–7 | |
| 18 | S30 | N | No | 0 | No | 53.6 | 157.5 | 5 | 117–243 | 2–4 | shortest trial 1.17 s |
| 19 | S31 | Y | Nd | 1 | Nd | 65.9 | 167.6 | 9 | 131–415 | 2–7 | gaps; WU10/11/13 |
| 20 | S32 | Y | Ip | 6 | No | 60.5 | 156.2 | 11 | 178–255 | 2–4 | |
| 21 | S34 | Y | online | 1 | Yes | 74.1 | 152.4 | 9 | 260–333 | 5–7 | only online-only case |
| 22 | S35 | N | No | 0 | No | 63.6 | 161.3 | 12 | 171–280 | 2–5 | most WU trials |
| 23 | S37 | Y | Ip | 2 | No | 63.2 | 156.2 | 9 | 251–373 | 4–7 | |
| 24 | S38 | Y | Ip | 5 | Yes | 66.8 | 160.0 | 9 | 246–343 | 5–7 | |
| 25 | S39 | N | No | 0 | No | 51.4 | 162.6 | 10 | 281–445 | 5–8 | |
| 26 | S40 | N | No | 0 | No | 61.4 | 165.1 | 8 | 257–393 | 4–7 | no WU06/08/10 |
| 27 | S41 | N | No | 0 | No | 52.3 | 154.9 | 8 | 201–314 | 4–6 | |
| 28 | S42 | N | No | 0 | No | 72.3 | 162.6 | 6 | 377–421 | 6–8 | |
| 29 | S43 | N | No | 0 | No | 68.6 | 161.3 | 6 | 236–290 | 4–6 | |
| 30 | S46 | Y | Nd | 2 | Nd | 52.7 | 158.8 | 9 | 194–378 | 4–7 | WU11, WU14 |
| 31 | S48 | N | No | 0 | No | 63.2 | 160.0 | 10 | 236–313 | 4–6 | no WU06/08 |

WU trial counts above are walking `WU*` trials only. S12 also has 10 extra `WK*Copy` takes that contain kinematics only (no event `Info` / `Res`).

---

## 9. MATLAB access

```matlab
load('data/processed/Data_structure_all_subs.mat', 'Dat')

Dat.S14.Survey                              % labels for subject 14
Dat.Survey                                  % all 31 rows
Dat.S14.New_Session.WU01.kinematics.LKneeAngles   % (frames × 3)
Dat.S14.New_Session.WU01.Info.KinFC         % foot-contact events
```

## 10. Python access (SciPy)

Kinematics and event arrays load as NumPy.

`Survey` strings and all `Res` tables are MATLAB MCOS objects — not numeric.

For labels in Python, read `data/raw/Victimization surveys.xlsx` and join on `Subject No`, or export `Dat.Survey` to CSV from MATLAB.

```python
from scipy.io import loadmat
import pandas as pd

mat = loadmat('data/processed/Data_structure_all_subs.mat',
              struct_as_record=False, squeeze_me=True)
knee = mat['Dat'].S14.New_Session.WU01.kinematics.LKneeAngles  # ndarray

survey = pd.read_excel('data/raw/Victimization surveys.xlsx')
# join on Subject No == 14
```

---

## 11. Known irregularities

| Item | Detail |
|---|---|
| S12 naming | Trials are `WU01Copy`… plus `WK01Copy`… (kinematics only). Calibration is `staticCopy`. |
| S17 naming | `WU0`, `WU3`–`WU7`, `WU9`, `WU11`, `WU13` — not zero-padded `WU01`. |
| Missing WU numbers | Several subjects skip trials (S14 has no WU02; S19 starts at WU02). |
| VictimType coding | Free text: `Ip` / `online` / `Both` / `Nd` / `No` (`online` is lowercase). |
| Times | Sometimes `Nd` even when Victimized = Y (S19, S26). |
| MATLAB tables | `Res`, `RawRes`, `Dat.Survey`, posture refs, and Survey strings need MATLAB to read as data. |
| No analog forces | `FPrate` is stored; force-plate channels are not in this file. |
| S15 height | 140.97 cm is an outlier vs the rest of the cohort (152–168 cm). |

---

## 12. ML notes

- Natural binary target: `Survey.Victimized` (17 Y vs 14 N).
- Features: `kinematics` and/or event timing, unless `Res` tables are exported from MATLAB first.
- n = 31 is small. Split **by subject** (leave-one-subject-out or nested CV). Do not randomly split trials, or the same person will leak into train and test.
