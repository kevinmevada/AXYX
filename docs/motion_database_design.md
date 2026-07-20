# MotionDatabase Design

**Status:** Design specification (pre-implementation)  
**Authority:** Bound to the production Motion Catalog in `metadata/motion_catalog/`  
**Dataset:** Filtered clinical gait dataset (`data/processed/Data_structure_filtered.mat`) — 31 subjects, 301 sessions  

This document defines the logical object model the MotionDatabase parser will expose. It does **not** rename or mutate the on-disk MATLAB dataset. Original session names and variable names are preserved.

---

## 1. Purpose

`MotionDatabase` is the authoritative in-memory / API layer over the filtered motion-capture MATLAB file. Downstream analysis code must depend on this model — not on ad-hoc `scipy.io.loadmat` navigation.

It turns the nested MATLAB hierarchy:

```text
Dat → Subject (S#) → Info / New_Session → Session → kinematics / Res
```

into typed objects with explicit ownership, validation rules, and documented unknowns (especially units).

---

## 2. Relationship Tree

```text
MotionDatabase
│
├── Subject
│      ├── Metadata
│      └── Sessions
│             ├── Marker
│             ├── JointAngle
│             ├── JointCenter
│             ├── COM                  (whole-body)
│             ├── SegmentCOM           (segment-level)
│             └── ClinicalMetric
│
└── Catalog references (read-only views of motion_catalog artifacts)
       ├── motion_schema.json
       ├── units.json
       ├── session_types.csv
       └── variable_catalog.csv
```

### Cardinality

| Relationship | Cardinality | Notes |
|---|---|---|
| MotionDatabase → Subject | 1 → N | N = 31 in filtered set |
| Subject → Metadata | 1 → 1 | From `Info` |
| Subject → Session | 1 → N | Session counts vary by subject |
| Session → Marker | 1 → N | Typically 37 unique names |
| Session → JointAngle | 1 → N | Typically 26 |
| Session → JointCenter | 1 → N | Typically 6 |
| Session → COM | 1 → 0..N | Whole-body COM fields |
| Session → SegmentCOM | 1 → 0..N | Segment COM fields |
| Session → ClinicalMetric | 1 → 0..N | From session `Res`; absent on some sessions |

---

## 3. MotionDatabase

### 3.1 What it owns

| Ownership | Description |
|---|---|
| Dataset path | Path to the filtered `.mat` file |
| Load state | Whether data is loaded; raw `Dat` handle (private) |
| Subjects | Map of subject ID → `Subject` |
| Schema contract | Parsed views of motion catalog (schema, units, session types) |
| Global assumptions | Explicit, documented; never inferred unsupported facts |

It does **not** own:

- Mutations of the `.mat` file
- Biomechanical analysis
- Unit conversion (units are Unknown until externally specified)
- Temporal gait-event interpretation (`KinFC` / `KinFO` / `Midsvnt` are absent)

### 3.2 Methods it exposes

```text
MotionDatabase
├── load(path=None) -> MotionDatabase
├── list_subjects() -> list[str]
├── get_subject(subject_id: str) -> Subject
├── has_subject(subject_id: str) -> bool
├── iter_subjects() -> Iterator[Subject]
├── validate() -> ValidationReport
├── statistics() -> DatabaseStatistics
├── session_types() -> list[SessionTypeRecord]
└── units_policy() -> UnitsPolicy
```

| Method | Responsibility |
|---|---|
| `load` | Load MATLAB file; build `Subject` graph; attach catalog contracts |
| `list_subjects` | Return sorted subject IDs present in `Dat` (excluding `Res`) |
| `get_subject` | Return typed `Subject` or raise if missing |
| `has_subject` | Membership check |
| `iter_subjects` | Iterate all subjects |
| `validate` | Structural validation against catalog expectations |
| `statistics` | Aggregate subject/session/frame/variable stats |
| `session_types` | Semantic session classification summary (labels only) |
| `units_policy` | Report Unknown (or explicit units if later discovered) |

### 3.3 How data is loaded

1. Resolve path (default: `data/processed/Data_structure_filtered.mat`).
2. Load with `scipy.io.loadmat` (or equivalent).
3. Require top-level `Dat` field; fail fast if absent.
4. Discover subject fields on `Dat` (all fields except global `Dat.Res`).
5. For each subject, construct `Subject` from `Info` + `New_Session`.
6. For each session, construct kinematics objects + clinical metrics from `Res`.
7. Detect trajectory layout per array: coordinate axis = dimension of size 3; remaining dimension = frame count. Support `(N, 3)` and `(3, N)`. Do not guess when ambiguous.
8. Attach catalog contracts from `metadata/motion_catalog/` (schema, units, session types).
9. Run lightweight validation; surface warnings (missing sessions, unresolved frames, etc.).

**Rule:** Original names are never renamed. Classification and categorization are labels overlaid on the source structure.

### 3.4 How subjects are accessed

```text
db = MotionDatabase().load()
ids = db.list_subjects()          # ["S2", "S3", ...]
subject = db.get_subject("S2")
for subject in db.iter_subjects():
    ...
```

Access is by stable subject ID strings as stored in MATLAB (`S2`, `S11`, …), not by integer index.

---

## 4. Subject

Represents one participant entry under `Dat.<SubjectID>`.

### 4.1 Ownership

```text
Subject
├── id: str                         # e.g. "S2"
├── metadata: Metadata
└── sessions: dict[str, Session]    # keyed by original session name
```

### 4.2 Methods

```text
Subject
├── list_sessions() -> list[str]
├── get_session(name: str) -> Session
├── sessions_by_class(classification: str) -> list[Session]
├── validate() -> ValidationReport
└── summary() -> SubjectSummary
```

### 4.3 Metadata

Source: `Subject.Info`.

| Field | Meaning | Notes |
|---|---|---|
| `FirstFrame` | Capture start frame index | Present for all subjects |
| `LastFrame` | Capture end frame index | Present for all subjects |
| `Vrate` | Video / mocap sampling rate | Consistent value: **100** |
| `FPrate` | Force-plate sampling rate | Consistent value: **1000** |
| `Mass` | Body mass | Numeric |
| `Height` | Standing height | Numeric |
| `LLegLength` | Left leg length | Numeric |
| `RLegLength` | Right leg length | Numeric |
| `RefThPosture` | Reference thorax posture | MATLAB object table (opaque) |
| `RefHdPosture` | Reference head posture | MATLAB object table (opaque) |

`Metadata` exposes these fields as attributes / a dict. Opaque MATLAB objects are retained as raw references without reinterpretation.

### 4.4 Sessions

- Keyed by **original session name** (`WU01`, `static`, `WK01Copy`, …).
- Session sets are **not required to be identical** across subjects.
- Semantic classification is available via catalog labels (see Session).

### 4.5 Validation

Per-subject checks:

- `Info` present and required numeric fields readable
- `New_Session` present
- At least one session constructible
- Sampling rates match database-wide expected values when present
- Warn on missing expected walking sessions (soft — not a hard failure)

### 4.6 Statistics

Per-subject aggregates:

- Session count
- Classification histogram
- Frame-count min / max / mean across sessions
- Marker / angle / metric inventory counts

---

## 5. Session

Represents one entry under `Subject.New_Session.<SessionName>` (excluding container-level `Res` / `RawRes` if present).

### 5.1 Ownership

```text
Session
├── name: str                       # original, preserved
├── classification: str             # semantic label only
├── subject_id: str
├── frame_count: int | None
├── trajectory_layout: "N,3" | "3,N" | None
├── sampling_rate_hz: float | None  # typically from subject Metadata.Vrate
├── markers: dict[str, Marker]
├── joint_angles: dict[str, JointAngle]
├── joint_centers: dict[str, JointCenter]
├── com: dict[str, COM]
├── segment_com: dict[str, SegmentCOM]
└── clinical_metrics: dict[str, ClinicalMetric]
```

### 5.2 Classification (labels only)

| Label | Meaning | Examples |
|---|---|---|
| Walking | Canonical walking trials | `WU01` … `WU14` |
| Calibration | Static / calibration | `static` |
| Walking Copy | Duplicate walking | `WU01Copy` |
| Calibration Copy | Duplicate calibration | `staticCopy` |
| Alternate Walking | Alternate naming | `WK01Copy`, `WU3` |
| Unknown | Unrecognized pattern | — |

Classification never renames the session. Inventory is **not** limited to WU01–WU09.

### 5.3 Markers

Dictionary of `Marker` objects from `session.kinematics` (marker-named fields).

### 5.4 Joint angles

Dictionary of `JointAngle` objects (fields matching angle naming patterns).

### 5.5 Joint centers

Dictionary of `JointCenter` objects (`*JC` fields).

### 5.6 COM

- **Whole-body:** `CentreOfMass`, `CentreOfMassFloor` → `COM`
- **Segment:** `PelvisCOM`, `LeftFemurCOM`, … → `SegmentCOM`

### 5.7 Clinical metrics

From `session.Res` — scalar / structured clinical outcome fields (e.g. `StpLen`, `WkVel`).  
**Not** temporal gait events. Expected events `KinFC`, `KinFO`, `Midsvnt` are absent.

### 5.8 Sampling rate

- Primary mocap rate: subject `Metadata.Vrate` (100 Hz in this dataset).
- Force-plate rate: subject `Metadata.FPrate` (1000 Hz) — informational; not implied on kinematic arrays.

Session exposes `sampling_rate_hz` as the mocap rate applicable to marker/angle trajectories.

### 5.9 Frame count

Derived by layout detection:

| Layout | Shape | Frames | Coordinate axis |
|---|---|---|---|
| `(N, 3)` | frames × XYZ | `N = shape[0]` | axis 1 |
| `(3, N)` | XYZ × frames | `N = shape[1]` | axis 0 |
| `(3, 3)` | ambiguous | `None` + warning | — |
| neither dim = 3 | unknown | `None` + warning | — |

**Never** assume `shape[0]` or `shape[1]` is time without detecting the size-3 axis.

Catalog observation (filtered set): frames range **11–460** (mean ≈ 270.65); all 301 sessions resolved.

---

## 6. Marker

| Property | Type | Description |
|---|---|---|
| `name` | `str` | Original marker label (e.g. `LFHD`, `RKNE`) |
| `xyz` | `ndarray` | Trajectory array, layout normalized or raw with layout flag |
| `n_frames` | `int \| None` | Non-coordinate dimension length |
| `layout` | `"N,3" \| "3,N" \| None` | Detected storage layout |
| `coordinate_system` | `str \| None` | Lab / anatomic frame if known; **None** if not in dataset |
| `units` | `str` | **`"Unknown"`** until catalog/external source specifies otherwise |

### Notes

- Typical set: 37 markers (full-body Plug-in Gait style names).
- Coordinate system is not explicitly stored in the `.mat` hierarchy today → leave `None` / `"Unknown"`, do not invent.
- Access helpers (implementation guidance): `as_n_by_3()` / `as_3_by_n()` for consumer convenience without mutating stored data.

---

## 7. JointAngle

| Property | Type | Description |
|---|---|---|
| `name` | `str` | e.g. `LKneeAngles`, `RHipAngles` |
| `series` | `ndarray` | Time series; typically shape with one size-3 axis |
| `n_frames` | `int \| None` | Layout-aware frame count |
| `rotation_axes` | `tuple[str, ...] \| None` | Axis labels if known (e.g. flexion/abduction/rotation); **None** if unspecified |
| `units` | `str` | **`"Unknown"`** (do not assume degrees) |

### Notes

- 26 unique joint-angle variables in the filtered catalog.
- Axis semantics are **not** declared in the MATLAB structure; `rotation_axes` remains unset unless an authoritative external mapping is supplied later.
- Same layout detection rules as markers when the series is 2D with an XYZ-like axis of size 3.

---

## 8. JointCenter

| Property | Type | Description |
|---|---|---|
| `name` | `str` | e.g. `LHJC`, `RKJC` |
| `xyz` | `ndarray` | Position trajectory |
| `n_frames` | `int \| None` | Layout-aware |
| `units` | `str` | **`"Unknown"`** |

Six centers in catalog: `LAJC`, `LHJC`, `LKJC`, `RAJC`, `RHJC`, `RKJC`.

---

## 9. COM / SegmentCOM

### Whole-body `COM`

| Property | Type | Description |
|---|---|---|
| `name` | `str` | `CentreOfMass` / `CentreOfMassFloor` |
| `xyz` | `ndarray` | Trajectory |
| `n_frames` | `int \| None` | Layout-aware |
| `units` | `str` | **`"Unknown"`** |

### `SegmentCOM`

Same shape as `COM`, with segment names (`PelvisCOM`, `LeftFemurCOM`, … — 15 in catalog).

---

## 10. ClinicalMetric

| Property | Type | Description |
|---|---|---|
| `name` | `str` | e.g. `StpLen`, `WkVel`, `FCKneeAtt` |
| `value` | `Any` | Scalar / nested MATLAB content as extracted |
| `description` | `str \| None` | Optional human description (catalog/external); default `None` |
| `units` | `str` | **`"Unknown"`** |

### Catalog metric names (10)

`FCKneeAtt`, `MSKneeAtt`, `MTC`, `MxStKneeAtt`, `NeckAng`, `StpLen`, `StpWth`, `Upright`, `WkVel`, `nUpright`

### Rules

- Sourced from `session.Res`, not from `kinematics`.
- Not treated as XYZ trajectories.
- Not treated as temporal gait events.
- Optional descriptions may be filled later from external clinical documentation; until then `description=None`.

---

## 11. Units Policy

Authoritative file: `metadata/motion_catalog/units.json`.

| Rule | Requirement |
|---|---|
| Default | Every category records `units = "Unknown"` |
| No guessing | Never assume millimeters or degrees |
| Extraction | If unit fields appear in future dataset revisions, extract them automatically |
| Parser duty | Expose Unknown explicitly; allow later override from external authoritative docs |

Applies to: markers, joint angles, joint centers, COM, segment COM, clinical metrics.

---

## 12. Validation

`MotionDatabase.validate()` / `Subject.validate()` produce a structured report:

| Check | Severity | Behavior |
|---|---|---|
| `Dat` present | Error | Fail load |
| Subject ID exists | Error | Fail `get_subject` |
| Marker layout resolvable | Warning | `frame_count=None` if not |
| Session count consistency across subjects | Warning | Expected — do not require equality |
| Missing expected walking sessions | Warning | Soft; use classification, not hard gates |
| Units missing | Info | Record Unknown |
| Temporal gait events absent | Info | Do not require KinFC/KinFO/Midsvnt |
| Sampling rate consistency | Warning/Error | Flag deviations from catalog norms |

---

## 13. Statistics

`MotionDatabase.statistics()` aggregates:

| Metric | Source |
|---|---|
| Subject count | Loaded subjects |
| Session count / unique names | Session graph |
| Classification histogram | Session labels |
| Frame min / max / mean / std | Layout-aware session frames |
| Variable counts by category | Markers, angles, centers, COM, metrics |
| Sampling rates observed | Metadata `Vrate` / `FPrate` |

These should reconcile with `metadata/motion_catalog/statistics.json` and `dataset_summary.md` after a controlled rebuild.

---

## 14. Explicit Non-Goals

- Writing or patching the `.mat` file
- Inferring biomechanical joint conventions
- Inferring coordinate frames or units
- Requiring identical session inventories per subject
- Treating `Res` clinical fields as gait events
- Hardcoding only WU01–WU09 as valid walking sessions

---

## 15. Implementation Binding (next phase)

When `MotionDatabase` is implemented, it must:

1. Depend on catalog artifacts under `metadata/motion_catalog/` as the schema contract.
2. Reuse (or share) layout detection logic consistent with `scripts/build_motion_catalog.py` (`detect_trajectory_layout`).
3. Preserve original names end-to-end.
4. Keep modules modular: `database`, `subject`, `session`, `variables`, `validation`, `statistics`.
5. Log unresolved layouts, missing sessions, and Unknown units explicitly.

---

## 16. Summary Diagram (ownership + access)

```text
MotionDatabase.load(path)
        |
        v
   list / get / iter ---------------> Subject(id)
                                         |
                          +--------------+--------------+
                          |                             |
                          v                             v
                      Metadata                      Sessions[name]
                   (Info fields)                        |
                                                        v
                                                    Session
                         +---------+--------+--------+----+----------+
                         |         |        |        |    |          |
                         v         v        v        v    v          v
                      Marker   JointAngle  Joint   COM  Segment   Clinical
                                         Center         COM       Metric

                         All variable units = "Unknown" unless catalog says otherwise
                         Frame count = non-XYZ dimension after layout detection
```

This is the final logical specification the MotionDatabase parser may safely implement against.
