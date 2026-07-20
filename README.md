# AXYX

**AXYX** is a research platform for clinical gait motion capture: ingest Vicon-style MATLAB sessions, reconstruct a full-body skeleton from markers, visualize playback in a scientific 3D viewport, and prepare animation for downstream engines (e.g. Unreal / MetaHuman).

| | |
|---|---|
| **Project** | AXYX |
| **Domain** | Biomechanics · clinical gait · scientific visualization |
| **Core library** | `motion_engine` (Python 3.11) |
| **Desktop app** | AXYX Studio (PySide6 + PyVista) |
| **Suggested Git remote** | `axyx` |

---

## Research goals

1. **Reproducible reconstruction** — marker → joint → bone graph driven by YAML, not ad-hoc scripts  
2. **Data fidelity** — joint positions and bone lengths derived only from the dataset  
3. **Interactive analysis** — subject/session browser, timeline playback, studio viewport  
4. **Export path** — scaffolding toward Unreal / MetaHuman pipelines  

---

## Repository layout

```
axyx/                          # git repo name (folder may still be V_ locally)
│
├── README.md                  # this file
├── CITATION.cff               # citation metadata
├── pyproject.toml             # project metadata
├── pytest.ini
├── run_axyx.bat / run_axyx.py # launch Studio
├── run_viewer.bat             # standalone viewer
│
├── config/                    # experiment & reconstruction configs (YAML)
│   ├── skeleton_definition.yaml
│   ├── bone_constraints.yaml
│   ├── coordinate_system.yaml
│   ├── subject_cohorts.yaml
│   └── unreal_config.yaml …
│
├── data/
│   ├── raw/                   # original MATLAB captures
│   └── processed/             # filtered working dataset
│
├── metadata/                  # catalogs, filter reports
├── notebooks/                 # exploratory analysis
├── docs/                      # design notes & figures
├── experiments/               # one-off research trials
├── results/                   # figures, exports, run outputs
│   ├── figures/
│   └── exports/
│
├── scripts/                   # dataset inspect / filter / validate
├── src/
│   └── motion_engine/         # core SDK + Studio UI
├── tests/
└── venv311/                   # Python 3.11 environment (not committed)
```

---

## Method (end-to-end)

```
MATLAB (.mat)
    → DatasetLoader / parser
    → MotionDatabase (subjects, sessions, markers, joint centers)
    → SkeletonBuilder  [config/skeleton_definition.yaml]
    → Skeleton + AnimationClip
    → AXYX Studio viewport (PyVista)
```

**Bone length** between parent joint **A** and child joint **B**:

```text
‖ B − A ‖₂   (Euclidean, per frame; mean over valid frames)
```

Joints are resolved from joint centers when available, otherwise from marker centroids (e.g. pelvis from LASI/RASI/LPSI/RPSI). No invented marker positions.

---

## Quick start

Requires **Python 3.11** (`venv311`) with PySide6, PyVista, NumPy, SciPy.

```bat
.\run_axyx.bat
```

Or:

```bat
set PYTHONPATH=src
set QT_API=pyside6
venv311\Scripts\python.exe run_axyx.py
```

1. Open a processed dataset  
2. Select subject → session in Explorer  
3. Inspect / play motion in the viewport  

Standalone viewer:

```bat
.\run_viewer.bat
```

Tests:

```bat
set PYTHONPATH=src
venv311\Scripts\python.exe -m pytest tests -q
```

---

## Software stack

| Component | Role |
|-----------|------|
| `motion_engine` | Domain models, MATLAB I/O, skeleton, animation, camera, renderer |
| AXYX Studio | Research UI — Explorer · Viewport · Timeline |
| PyVista / VTK | Real-time 3D scientific visualization |
| YAML configs | Skeleton topology, constraints, Unreal mapping |

---

## Citing

If you use AXYX in academic work, please cite this repository (see `CITATION.cff`).

```bibtex
@software{axyx,
  title        = {AXYX: Clinical Gait Motion Research Platform},
  author       = {{AXYX Contributors}},
  year         = {2026},
  url          = {https://github.com/<org>/axyx}
}
```

---

## Status

Active research / engineering prototype. Viewport and Studio UI are demonstration-ready; Unreal export remains under active development.

---

## License

Add a license before public release (e.g. MIT or Apache-2.0).
