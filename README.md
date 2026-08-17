# AXYX

Research platform for **clinical gait** motion capture: ingest Vicon-style MATLAB sessions, reconstruct a full-body skeleton, play it in **AXYX Studio**, and run a certified **ML research pipeline** on the same cohort.

| | |
|---|---|
| **Library** | `motion_engine` · Python 3.11 |
| **App** | AXYX Studio (PySide6 + PyVista) |
| **Studio dataset** | `data/processed/Data_structure_filtered.mat` · 31 subjects · ~301 sessions |
| **ML dataset** | `data/processed/Data_structure_all_subs.mat` · 31 females · survey-joined |
| **Repo** | [kevinmevada/AXYX](https://github.com/kevinmevada/AXYX) |

---

## What we are doing

Two tracks share the same capture lab but different questions:

| Track | Question | Entry |
|---|---|---|
| **Studio** | Can we reconstruct and **visualize** Plug-in Gait trials interactively? | `run_axyx.py` → open `.mat` |
| **ML research** | Do victimized vs non-victimized females show a **shared, robust gait difference** (Phases 0–6 + Similarity P0)? | [`ml/README.md`](ml/README.md) |

Studio uses `MotionDatabase` as the typed object graph (`motion_engine`). The ML track uses `gait_research` under `ml/src/` — audit → cycles → features → statistics → phenotypes → trajectories → similarity tests. **Neither track trains a victim classifier** on this *n* = 31 sample.

**ML bottom line (certified):** no robust victim-associated shared gait signature after FDR, LOSO, trajectory tests, and the full P0 similarity battery. Details: [`ml/results/similarity/p0_synthesis.md`](ml/results/similarity/p0_synthesis.md).

---

## How it works

### Studio visualization

```
.mat  (top-level Dat)
    → MotionDatabaseLoader
    → MotionDatabase → Subject → sessions.kinematics
    → SkeletonBuilder  [config/skeleton_definition.yaml]
    → Skeleton + AnimationClip
    → AXYX Studio viewport (PyVista)
```

### ML research pipeline

```
data/raw MAT + Victimization surveys.xlsx
    → Phase 0 audit
    → Phase 1 gait cycles (880 × 101 points)
    → Phase 2 features (label-blind)
    → Phases 3–6 group stats, phenotypes, within-victim structure, trajectories
    → Similarity P0.1–P0.6 (shared-pattern discovery)
    → ml/results/
```

Run commands and phase docs: **[`ml/README.md`](ml/README.md)**.

---

## Data required for visualization (Studio)

Studio **only loads MATLAB `.mat`** with the `Dat` hierarchy. Welcome may list `.c3d` / `.trc` / `.npz`; those are **not parsed yet**.

```text
data/processed/Data_structure_filtered.mat
```

| Requirement | Detail |
|---|---|
| Top-level key | **`Dat`** (required) |
| Subjects | `Dat.S2`, `Dat.S11`, … |
| Per subject | `Info` + `New_Session` |
| Per trial | `kinematics` struct, 2D XYZ arrays `(N, 3)` or `(3, N)` |

```text
.mat
└── Dat
      └── S2
            ├── Info                 Mass, Height, Vrate, FPrate, leg lengths
            └── New_Session
                  └── WU01
                        └── kinematics   LASI, LHJC, LKneeAngles, …
```

### Stick figure needs (Plug-in Gait names)

Pelvis: `LASI` `RASI` `LPSI` `RPSI` · Hips: `LHJC`/`RHJC` · Knees: `LKNE`/`RKNE` · Ankles: `LANK`/`RANK` · plus trunk/head/arm markers per [`config/skeleton_definition.yaml`](config/skeleton_definition.yaml).

`Info` supplies mass, height, rates. Age, sex, victimization live in **survey Excel** (`data/raw/Victimization surveys.xlsx`) — used by ML, not required for 3D playback.

### Will not visualize

CSV/Excel kinematics, C3D/TRC/NPZ, wrong marker names, or arrays without a size-3 XYZ axis.

---

## Data required for ML (research track)

Place under repo **`data/`** (shared, not inside `ml/`):

| File | Role |
|---|---|
| `data/raw/Data_structure_all_subs.mat` | Original 43-subject capture |
| `data/raw/Victimization surveys.xlsx` | Labels — join on **`Subject No`** ↔ `Dat.S{n}` |
| `data/processed/Data_structure_all_subs.mat` | 31-female working MAT with survey joined |

Same `.mat` contract as Studio (`Dat → S# → New_Session → kinematics`). ML phases read MATLAB once, then work from `ml/results/` (npz, parquet, csv).

---

## Quick start

### Studio

```bat
.\run_axyx.bat
```

Or:

```bat
set PYTHONPATH=src
set QT_QPA_PLATFORM=windows
venv311\Scripts\python.exe run_axyx.py
```

Open `data/processed/Data_structure_filtered.mat` → pick subject → session → play.

### ML (smoke test)

```bat
venv311\Scripts\python.exe ml\scripts\audit_dataset.py
set PYTHONPATH=ml\src
venv311\Scripts\python.exe -m pytest ml\tests\similarity -q
```

Install extras if needed: `pip install pyarrow matplotlib tqdm openpyxl numba`

### Tests (motion engine)

```bat
set PYTHONPATH=src
venv311\Scripts\python.exe -m pytest tests -q
```

---

## Repository layout

```
AXYX/
├── data/raw/                 captures + survey Excel
├── data/processed/           filtered .mat (Studio + ML)
├── config/                   skeleton YAML (Studio)
├── metadata/motion_catalog/  variable catalog
├── ml/                       ★ ML research (Phases 0–6 + Similarity P0)
│   ├── README.md             full methods + results index
│   ├── scripts/              phase runners
│   ├── src/gait_research/    analysis library
│   ├── tests/
│   └── results/              certified outputs
├── src/motion_engine/        SDK + AXYX Studio
├── docs/                     architecture specs
├── tests/                    motion_engine tests
└── run_axyx.py
```

---

## Stack

| Component | Role |
|---|---|
| `motion_engine` | MATLAB I/O, `MotionDatabase`, skeleton, Studio UI |
| `gait_research` (`ml/src/`) | Gait-cycle extraction, features, statistics, similarity |
| PyVista / VTK | 3D visualization |
| YAML | Skeleton topology |

---

## Citing

See `CITATION.cff`.

```bibtex
@software{axyx,
  title  = {AXYX: Clinical Gait Motion Research Platform},
  author = {{AXYX Contributors}},
  year   = {2026},
  url    = {https://github.com/kevinmevada/AXYX}
}
```

---

## Status

- **Studio:** demonstration-ready for Plug-in Gait `.mat` catalogs in the `Dat` shape above.
- **ML:** Phases 0–6 and Similarity P0 **complete / certified**; P1 and predictive modeling **not started**.
- C3D/TRC ingest and SceneGraph-driven renderer: not done.
