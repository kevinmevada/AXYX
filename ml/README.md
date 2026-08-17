# AXYX ML research (`ml/`)

Part of the [AXYX](https://github.com/kevinmevada/AXYX) monorepo. **Studio** visualizes gait via `motion_engine` + `data/processed/Data_structure_filtered.mat`. **This track** runs the certified Phases 0–6 + Similarity P0 statistical pipeline on the female cohort MAT + survey Excel.

Research codebase for asking whether **female gait kinematics** contain a **shared, robust, interpretable difference** between people with versus without a victimization history.

The project is **not** a victim classifier. Work proceeds in two layers:

1. **Phases 0–6** — audit, cycle extraction, features, group statistics, unsupervised phenotypes, within-victim Euclidean structure, and time-resolved trajectories. **No XGBoost, neural net, or “victim score” has been trained.** Predictive modeling was deliberately deferred because *n* = 31 independent people.
2. **Similarity P0 battery (P0.1–P0.6)** — after Phases 0–6 were frozen, a separate package tested whether victims share a pattern *with each other* that controls do not (direction, abnormality set, shape, event-phase windows, confound residualization, CRP coupling). Phases 0–6 outputs were **not** modified.

**Current scientific bottom line:** after subject-level analyses with multiplicity control, robustness checks, trajectory tests, **and** the full P0 similarity battery (all null after residualization / FDR / LOSO), **no robust victim-associated shared gait signature was detected** in this sample. See `results/similarity/p0_synthesis.md`. **P1 (Wasserstein / RV / soft-DTW / common subspace) has not been started** and should not be without explicit go-ahead.

---

## 1. Scientific question

Primary question (Phases 0–6):

> Which biomechanical gait characteristics, if any, show statistically supported, robust, interpretable, and subject-consistent differences between victimized and non-victimized females?

Secondary question (Similarity P0 — after the first layer was null):

> Do the 17 victimized women share a locomotor pattern *with each other* that controls do not — a shared deviation direction, abnormality set, waveform shape, phase-localized signature, or inter-joint coupling — that univariate mean differences can miss?

Neither is the same as:

> Can a model predict victimization from gait at high accuracy?

With 31 people and thousands of features, a classifier can overfit easily. This repository first asks whether a **shared pattern** exists. If the data do not show one, that result is reported honestly.

### What “independent unit” means

| Quantity | Role |
|---|---|
| **31 subjects** | Independent sampling units for inference |
| **17 victimized / 14 control** | Group labels (`Y` / `N`) |
| **260 walking trials** | Repeated sessions within people |
| **880 gait cycles** | Repeated measures within people — **not** 880 independent samples |

Treating 880 cycles as independent (“pseudo-replication”) would inflate sample size and produce false confidence. Every inferential step in Phases 3–6 and Similarity P0 permutes or compares **subjects**.

---

## 2. Cohort and data

| Item | Value |
|---|---|
| Sex | Females only in the processed file |
| Subjects | 31 (`S2`–`S5`, `S7`–`S9`, `S11`–`S15`, `S17`, `S19`, `S23`, `S26`, `S27`, `S30`–`S32`, `S34`, `S35`, `S37`–`S43`, `S46`, `S48`) |
| Labels | 17 victimized (`Y`), 14 not (`N`) |
| Capture | Plug-in Gait, **100 Hz** kinematics |
| Walking trials | 260 `WU*` trials |
| Gait cycles | 880 (440 left, 440 right), time-normalized to **101 points (0–100%)** |
| Anthropometry | Mass ~48–100 kg; height ~141–168 cm (S15 is a short outlier) |

**Join key:** Excel column **`Subject No`** ↔ MATLAB `Dat.S{n}`. Do **not** join on Excel column `No` (that is only a 1–31 roster index).

**KinFC side encoding (measured, not assumed):** code `1` = **right**, code `2` = **left**.

**Axes:** spatial and angle axes are stored as **`ax1` / `ax2` / `ax3`**. They are **not** certified as AP / ML / vertical. Do not relabel them without a separate coordinate-convention study.

### Files (shared repo `data/`)

| Path | Role |
|---|---|
| `data/raw/Data_structure_all_subs.mat` | Original 43 subjects (31 F + 12 M) |
| `data/raw/Victimization surveys.xlsx` | Survey labels |
| `data/processed/Data_structure_all_subs.mat` | **31 females**, survey joined onto each `Dat.S{n}` |
| `data/processed/Data_structure_filtered.mat` | Studio / Motion Engine working file (same cohort, filtered sessions) |
| `ml/docs/AXYS_processed_dataset_blueprint.md` | Dataset layout and field map |

Males were removed in the processed MAT (S6, S10, S18, S21, S22, S25, S29, S33, S36, S45, S47, S50). Irregular session names (`WU0`, `WU01Copy`, etc.) are **not** renamed.

---

## 3. Pipeline overview

```
raw MAT + survey
        │
        ▼
Phase 0  Dataset audit          (what exists; labels; quality)
        │
        ▼
Phase 1  Gait events & cycles   (880 cycles, 0–100%, 101 points)
        │
        ▼
Phase 2  Feature discovery      (label-blind; 714 cycle / 3665 subject columns)
        │
        ▼
Phase 3  Group statistics       (screen → effect sizes → FDR → robustness)
        │
        ▼
Phase 4  Phenotypes             (unsupervised clusters; labels after freeze)
        │
        ▼
Phase 5  Within-victim structure (Euclidean compactness)
        │
        ▼
Phase 6  Trajectory FDA         (subject-median curves; cluster permutation)
        │
        ▼
 ★ Phases 0–6 FROZEN ★
        │
        ▼
Similarity P0  Cross-cohort similarity discovery
        │  P0.1 deviation cosine
        │  P0.2 abnormality Jaccard
        │  P0.3 shape Pearson/DTW
        │  P0.4 event-phase windows
        │  P0.5 confound residualization (folded into each test)
        │  P0.6 Hilbert CRP coupling
        │  → p0_synthesis.md
        │
        ▼
P1 / Phase 7  NOT STARTED       (no Wasserstein/RV/soft-DTW; no predictive ML)
```

**Hard rules across phases and Similarity P0**

- Victimization labels are **not** used to build features, scale, PCA, choose clusters, or pick which curves/pairs/phases to test (those lists are **pre-registered** before looking at group results).
- Labels **are** used for victim/control tests and for the similarity statistics among the labeled victim subset, only after the relevant representation is frozen.
- Do not manufacture a signature if FDR, robustness, or consistency fail.
- Do not train classifiers “to prove” a gait exists.
- Similarity P0 **must not** rewrite Phase 0–6 pipelines or certified outputs.

---

## 4. Phase results (certified / completed)

### Phase 0 — Dataset audit

**Status:** PASS WITH WARNINGS  

Read-only audit of the processed MAT: 31 subjects, 17/14 labels, 260 walking trials, 100 Hz, events present. Some arm-marker NaNs (e.g. S30 missing LUPA) do **not** invalidate lower-body cycles.

- Code: `src/gait_research/` (`catalog.py`, `matio.py`, `sessions.py`, `audit.py`, `labels.py`)
- Run: `python scripts/audit_dataset.py`
- Out: `results/phase0/`, `docs/phase0_dataset_audit.md`

### Phase 1 — Gait events and cycles

**Status:** PASS  

Ipsilateral foot-contact to next ipsilateral contact. **880** usable lower-body cycles, normalized to 101 points. Cycle duration roughly 0.88–1.32 s (median ~1.04 s). Cycle counts are uneven (e.g. S19 = 4, S30 = 3).

Stored per-cycle events (all 880 complete; strict temporal order): IC → opposite FO → mid-stance (`Midsvnt`) → opposite FC → ipsilateral FO → next IC. These bound clinical phases for Similarity P0.4.

- Run: `python scripts/extract_gait_cycles.py`
- Out: `results/phase1/` including `gait_cycle_inventory.csv` and `gait_cycles/normalized_core.npz` shape `(880, 26, 101, 3)`
- Core signals: pelvis ASI/PSI, hip/knee/ankle joints and angles, heel/toe, foot progression, COM / COM floor  
  (**Note:** `LPelvisAngles` / `RPelvisAngles` are **not** in the Phase 1 core cube; pelvis is represented by markers.)

### Phase 2 — Features (label-blind)

**Status:** PASS (certified)  

Victimization is **never** used in feature calculation. Default subject central tendency is **`*__median`**.

| Level | Size |
|---|---|
| Cycle features | 880 × **714** numeric |
| Subject table | 31 × **3665** (4 IDs + 714×5 aggregations + 91 symmetry/variability) |
| Catalog | **805** specs (714 cycle + 91 subject extras) |

Families (catalog): kinematic 390, phase 240, spatial 64, symmetry 58, variability 33, temporal 9, coordination 8, smoothness 3.

Derivatives: Savitzky–Golay **window 11, poly 3**. ROM/min/max unsmoothed. Spatial axes remain ax1/ax2/ax3. Symmetry is **ipsilateral** (L-cycle left limb vs R-cycle right limb).

- Run: `python scripts/run_phase2.py` then `python scripts/certify_phase2.py`
- Out: `results/phase2/cycle_features.parquet`, `subject_features.parquet`, `feature_catalog.json`

### Phase 3 — Statistical signature discovery

**Status:** COMPLETE / PASS WITH WARNINGS  

Label-independent quality + redundancy on `*__median` / `var_*` / `sym_*`, **then** 17 vs 14 comparison. Cliff’s δ, Mann–Whitney, Benjamini–Hochberg FDR, leave-one-**subject**-out, subject-label permutation (seed `20260813`, 999 shuffles).

| Gate | Result |
|---|---|
| Analysis columns | 805 |
| Passed quality screen | 743 |
| Redundancy representatives | 335 |
| FDR ≤ 0.05 | **0** |
| FDR ≤ 0.10 | **0** |
| Pre-specified signature rule | **0** hits |

Signature rule (all required): FDR q ≤ 0.10, \|Cliff’s δ\| ≥ 0.33, LOSO direction ≥ 0.80, victim directional consistency ≥ 0.60.

Uncorrected permutation *p*-values can look small; after 335 tests they do **not** survive FDR. Exploratory top-20 ranks exist for later validation only — they are **not** a confirmed victim gait.

- Run: `python scripts/run_phase3.py`
- Tests: `python -m pytest tests/phase3 -q` (16 passed when last run)

### Phase 4 — Phenotypes (unsupervised)

**Status:** COMPLETE / PASS WITH WARNINGS  

Family-balanced compact representation (31 × **27** dimensions from 335 representatives). Hierarchical Ward; *k* chosen **without** labels (silhouette, min size ≥ 4, bootstrap ARI ≥ 0.50).

Selected split: **27 vs 4** (S5, S19, S35, S40). Composition **15/12** vs **2/2** victimized/control. Fisher *p* = 1, permutation *p* = 1. Height Kruskal *p* ≈ 0.05 (possible stature confounding). This is a **majority/outgroup** split, not two large victim-related gait types.

- Run: `python scripts/run_phase4.py`

### Phase 5 — Within-victim similarity

**Status:** COMPLETE / PASS WITH WARNINGS  

| Statistic | Value |
|---|---|
| Mean pairwise distance (17 victims) | 20.42 |
| Random groups of 17 (null mean) | 20.06 |
| Similarity permutation *p* | **0.547** |
| Victim 1-NN is another victim | 52.9% (null 53.6%, *p* = 0.615) |
| All victims vs controls centroid *p* | **0.771** |
| Stable victim subgroups | **0** (rejected 15+2 as min size &lt; 4) |

Victims are not a tight neighborhood in gait space.

- Run: `python scripts/run_phase5.py`
- Tests: `python -m pytest tests/phase5 -q` (8 passed when last run)

### Phase 6 — Time-resolved trajectories

**Status:** COMPLETE / PASS WITH WARNINGS  

Subject-level **nanmedian** curves (31 × 101), cluster-based permutation of **subject labels** (primary 9999 permutations). Welch *t* cluster mass; BH within analysis family. Shape descriptors use the same SG 11/3 as Phase 2.

| Item | Result |
|---|---|
| Channels tested | 86 |
| Missingness exclusions | 0 |
| **ROBUST** regions | **0** |
| **EXPLORATORY** (cluster *p* &lt; 0.05) | **0** |
| Strongest unsupported cluster | `RHipAngles_ax1` 77–83%, δ ≈ 0.43, perm *p* = 0.147, bootstrap CI includes 0 |

Aggregation into Phase 2/3 scalars was **not** hiding a clear localized trajectory effect.

- Run: `python scripts/run_phase6.py`
- Tests: `python -m pytest tests/phase6 -q` (12 passed when last run)

### Phase 7 / Similarity P1

**Not started.** Do not claim predictive accuracy on this *n* without a new, pre-registered design (and preferably new subjects). Do not start Wasserstein / RV / soft-DTW / common-subspace discovery on these same 31 subjects without go-ahead (see §5.7).

---

## 5. Similarity P0 — cross-cohort shared-pattern discovery (COMPLETE / ALL NULL)

### 5.0 Motivation and design rules

Phases 3–6 asked whether victims **differ from controls** (means, clusters, Euclidean compactness, trajectory clusters). All were null or non-enriching. That does **not** automatically answer a different question:

> Even if victims are not close to each other in Euclidean space, and even if no feature mean differs after FDR, do victims still share a *relative* pattern among themselves?

Package: `src/gait_research/similarity/`.  
Outputs: `results/similarity/`.  
Synthesis: `results/similarity/p0_synthesis.md`.

| Convention | Choice |
|---|---|
| Unit | **Subject** (n=31) |
| Null | Shuffle victim/control **labels** across subjects (≥9999) |
| Seed | `20260813` |
| Confounds | Height, mass, mean leg length, subject-median cycle duration — residualize **before** the primary gate |
| Pre-registration | Feature/curve/phase/pair lists locked in JSON **before** real tests |
| Decision gate | Post-residual primary; LOSO + FDR where applicable; stop and report before the next P0.* |
| Classifiers | Never used as discovery tools |

**P0.5** in the original plan (“confound as shared residual pattern”) was **not** implemented as a separate discovery script. The same residualization was the **primary evidence gate** inside P0.1–P0.4 and P0.6.

### 5.1 P0.1 — Deviation-direction alignment

**Question:** Do victims share a common *direction* of deviation from the control centroid in Phase 4’s 27-D family-PC space?

**Statistic:** For each subject, \(d_i = x_i - \overline{x}_{\text{controls}}\). Mean pairwise **cosine** among the 17 victim \(d_i\).

**Code / run / out**

- `src/gait_research/similarity/deviation.py`, `load.py`
- `python scripts/run_p01_deviation.py`
- `results/similarity/p01_deviation/` (`summary.csv`, `p01_report.md`, cosine heatmap, PCA of deviations, permutation null)
- Tests: `python -m pytest tests/similarity/test_deviation.py -q`

**Post-residual result (primary):** mean pairwise cosine **0.052** vs null mean **0.110**, perm *p* = **0.758**, LOSO pass. Observed &lt; null → victims are *less* directionally aligned than random groups of 17.

**Decision: NULL.**

### 5.2 P0.2 — Shared abnormality-set overlap

**Question:** Do victims share *which* features fall outside the control band (a discrete abnormality set), even if continuous directions do not align?

**Pre-registration:** 30 locked features in `results/similarity/p02_abnormality/preregistered_features.json` (ROM ax1 bilateral, peak/min timing, stance/cycle/mid-stance, COM/path3d, 4 coordination corr+lag). No post-hoc search of the 3665-column matrix.

**Method:** Control 10th–90th percentile band (14 controls only) → binary exceedance → mean pairwise **Jaccard** among 17 victims. Per-feature co-exceedance + BH-FDR across the 30. Residualize continuous features **before** binarizing.

**Code / run / out**

- `src/gait_research/similarity/abnormality.py`
- `python scripts/run_p02_abnormality.py`
- `results/similarity/p02_abnormality/` (fingerprint heatmaps, co-exceedance tables, `p02_report.md`)
- Tests: `python -m pytest tests/similarity/test_abnormality.py -q`

**Post-residual result:** Jaccard **0.191** ≈ null **0.201**, perm *p* = **0.603**, **0** features with co-exceedance FDR q ≤ 0.10, LOSO top-5 feature-rank unstable.

**Decision: NULL.**

### 5.3 P0.3 — Amplitude-normalized waveform shape

**Question:** Do victims share *shape/timing* of core curves after discarding ROM/amplitude (what P0.1’s PC magnitudes and P0.2’s thresholds do not isolate)?

**Pre-registration:** 12 curves in `results/similarity/p03_shape/preregistered_curves.json` — hip/knee/ankle/foot-progress L/R ax1, LASI/RASI ax1 (Phase-1 pelvis proxies), COM ax1+ax3. Loaded from Phase 1 `normalized_core.npz` via subject nanmedian.

**Normalization:** Per subject, per curve: **z-score across the 101 phase points** (zero mean, unit variance). Explicitly strips amplitude; same representation feeds both measures.

**Statistics (reported separately, never averaged):**

1. Mean over curves of mean pairwise **Pearson** among victims  
2. Mean over curves of mean pairwise **DTW** distance (pure NumPy / numba DTW)

**Code / run / out**

- `src/gait_research/similarity/shape_space.py`
- `python scripts/run_p03_shape.py`
- `results/similarity/p03_shape/` (overlays, null histograms, `p03_report.md`)
- Tests: `python -m pytest tests/similarity/test_shape_space.py -q`

**Post-residual result:** Pearson **−0.023** (null −0.030), *p* = **0.267**; DTW **7.657** (null 7.591), *p* = **0.629**; 0 FDR survivors. Pre-residual Pearson ~0.55 matched the null (~0.55) — generic shared gait shape, not victim-specific.

**Decision: NULL.**

**Cycle duration × DTW note (documented in report):** residualizing cycle duration removes linear associations with phase-% values; DTW on 0–100% curves already allows nonlinear warping. Different timing constructs; both kept after the same residualization.

### 5.4 P0.4 — Event-localized phase windows

**Question:** Is similarity localized to clinical gait phases that whole-cycle tests dilute?

**Phase audit (locked before testing):** From Phase 1 inventory, all 880 cycles have IC, opposite FO, mid-stance, opposite FC, ipsilateral FO, next IC in strict order.

| Reconstructable | Not reconstructable (not estimated) |
|---|---|
| Loading response (IC → opp FO) | Initial swing |
| Mid-stance (opp FO → Midsvnt) | Mid-swing |
| Terminal stance (Midsvnt → opp FC) | Terminal swing |
| Pre-swing (opp FC → ipsi FO) | |
| Swing undivided (ipsi FO → next IC) | |

Locked in `results/similarity/p04_event_phases/preregistered_phases.json`.

**FDR family (stated before running):**  
**240** = 5 phases × 12 P0.3 curves × 2 aggregations (mean, rom) × 2 tests (deviation cosine, abnormality Jaccard). BH-FDR spans the **entire** family (not per-window). Windowing layer reuses `deviation.py` / `abnormality.py`.

**Code / run / out**

- `src/gait_research/similarity/event_phases.py`
- `python scripts/run_p04_event_phases.py --n-perm 9999`
- `results/similarity/p04_event_phases/` (cell tables, heatmaps, window multivariate + LOSO, `p04_report.md`)
- Tests: `python -m pytest tests/similarity/test_event_phases.py -q`

**Post-residual result:** **0 / 240** cells with FDR q ≤ 0.10 (min raw perm *p* = 0.0188 — expected under many comparisons).

**Decision: NULL.**

### 5.5 P0.5 — Confound residualization (folded in)

Not a standalone discovery script. For every P0 test, continuous inputs were residualized on **height_cm, mass_kg, mean_leg_cm, cycle_duration_s_median** (subject-level OLS with intercept) **before** the primary similarity statistic. Pre- and post-residual results are always reported; the **gate uses post-residual**.

### 5.6 P0.6 — Continuous relative phase (CRP) coordination

**Question:** Do victims share *inter-joint coupling* independent of each joint’s marginal position/timing/shape (structurally invisible to P0.1–P0.4)?

**Velocity audit:** Phase 1 stores angle trajectories only (no angular-velocity channel). Finite-difference / SG velocity can be derived (Phase 2 does for features) but is **unused** for Hilbert CRP.

**CRP method (Hilbert):** Instantaneous phase from the Hilbert analytic signal of the **demeaned** ax1 angle (`scipy.signal.hilbert` → `np.angle`). Preferred over `atan2(ω, θ)` because phase-plane methods need separate position/velocity normalization.  
CRP = `wrap(φ_proximal − φ_distal)` to (−π, π]. Subject profile = circular mean across cycles.

**Pre-registration:** 6 pairs in `results/similarity/p06_coordination/preregistered_pairs.json` — hip–knee, knee–ankle, hip–ankle × L/R.

**Statistics:**

1. Circular similarity `mean_t cos(CRP_i − CRP_j)` (preserves constant phase offsets that z-scored Pearson would destroy)  
2. DTW on `unwrap(CRP − CRP[0])`  

FDR family = **12** (6 pairs × 2 measures).

**Code / run / out**

- `src/gait_research/similarity/coordination_crp.py`
- `python scripts/run_p06_coordination.py`
- `results/similarity/p06_coordination/` (CRP overlays, nulls, `p06_report.md`)
- Tests: `python -m pytest tests/similarity/test_coordination_crp.py -q`

**Post-residual result:** circular **0.649**, perm *p* = **0.929**; DTW **17.63**, *p* = **0.605**; **0 / 12** FDR survivors. High absolute circular similarity (~0.65–0.84) reflects **generic shared gait coordination**, not victim-specific excess over the permutation null.

**Decision: NULL.**

### 5.7 P0-family synthesis and stop rule

| ID | Construct | Gate |
|---|---|---|
| P0.1 | Deviation direction | **NULL** |
| P0.2 | Abnormality set | **NULL** |
| P0.3 | Waveform shape | **NULL** |
| P0.4 | Event-phase localized | **NULL** |
| P0.5 | Confound residualization | Folded into each test |
| P0.6 | CRP coupling | **NULL** |

**Honest conclusion for this sample:** no defensible shared victim locomotor signature under the pre-registered P0 program.

**Recommendation:** Do **not** start P1 on these same 31 subjects without go-ahead. Escalating to Wasserstein / RV / soft-DTW / common subspace after six null gates would be exploratory dredging unless there is a new, independently motivated hypothesis and preferably an **external cohort**.

Full write-up: `results/similarity/p0_synthesis.md`.

---

## 6. Repository layout

```
AXYX/
├── data/raw/ … data/processed/     # shared captures (not under ml/)
└── ml/
    ├── README.md                   # this file
    ├── scripts/                    # phase runners
    ├── src/gait_research/          # library (paths.py → repo data/)
    ├── tests/
    ├── docs/
    └── results/                    # phase0–6 + similarity outputs
```

Do **not** modify a completed phase’s pipeline or certified outputs when adding later work. Similarity P0 only *reads* Phase 1–4 artifacts.

---

## 7. How to run

From the **AXYX repo root**, using the project venv (`venv311`). Scripts live under `ml/scripts/` and prepend `ml/src` automatically. **Data** is read from repo `data/`; **outputs** write to `ml/results/`.

```bat
cd C:\path\to\AXYX
venv311\Scripts\python.exe ml\scripts\audit_dataset.py

REM Phases 0–6 (frozen; re-run only to regenerate certified outputs)
venv311\Scripts\python.exe ml\scripts\extract_gait_cycles.py
venv311\Scripts\python.exe ml\scripts\run_phase2.py
venv311\Scripts\python.exe ml\scripts\certify_phase2.py
venv311\Scripts\python.exe ml\scripts\run_phase3.py
venv311\Scripts\python.exe ml\scripts\run_phase4.py
venv311\Scripts\python.exe ml\scripts\run_phase5.py
venv311\Scripts\python.exe ml\scripts\run_phase6.py

REM Similarity P0 (does not rewrite Phases 0–6)
venv311\Scripts\python.exe ml\scripts\run_p01_deviation.py
venv311\Scripts\python.exe ml\scripts\run_p02_abnormality.py
venv311\Scripts\python.exe ml\scripts\run_p03_shape.py
venv311\Scripts\python.exe ml\scripts\run_p04_event_phases.py --n-perm 9999
venv311\Scripts\python.exe ml\scripts\run_p06_coordination.py
venv311\Scripts\python.exe ml\scripts\run_power_analysis.py
```

Tests (from repo root):

```bat
set PYTHONPATH=ml\src
venv311\Scripts\python.exe -m pytest ml\tests\phase0 ml\tests\test_phase1_cycles.py ml\tests\phase2 ml\tests\phase3 ml\tests\phase4 ml\tests\phase5 ml\tests\phase6 -q
venv311\Scripts\python.exe -m pytest ml\tests\similarity -q
```

**Reproducibility:** stochastic steps use seed **`20260813`** unless a script documents otherwise. Similarity P0 primary permutations use **9999** subject-label shuffles. The P0.1 MDE simulation uses **999** perms × **1000** datasets per λ (documented in `results/similarity/power_analysis/mde_report.md`).

### Environment

Developed on Windows with Python 3, including:

- `numpy`, `pandas`, `scipy`, `pyarrow`
- `matplotlib`
- `scikit-learn` (Phase 4/5 clustering / ARI)
- `tqdm` (P0.4 progress bars)
- `numba` (optional; speeds P0.3 DTW and P0.4 1-D perm loops)
- MATLAB is used only as the original kinematics store; Phase 1+ work from exported npz/parquet

---

## 8. Methods cheat sheet

| Topic | Choice in this repo |
|---|---|
| Cycle definition | Ipsilateral FC → next ipsilateral FC |
| Time base | 0–100% gait cycle, 101 samples |
| Subject summary | Median across that person’s cycles (circular mean for CRP) |
| Default features for stats | `*__median`, plus dedicated `var_*` / `sym_*` |
| Effect size | Cliff’s δ (plus robust median/IQR where reported) |
| Multiplicity | Benjamini–Hochberg FDR; cluster permutation for Phase 6 curves; P0.4 family-wide FDR (240 cells) |
| Permutation unit | **Subject** (never shuffle isolated cycles or isolated time points as if they were people) |
| Consistency | Share of victims on the group-difference side of the control median; LOSO sign / rank stability in P0 |
| Confounds (P0) | OLS residualize height, mass, mean leg, cycle duration before primary gate |
| Coordinates | `ax1/ax2/ax3` until certified |
| Smoothing | SG 11, 3 for derivatives/smoothness; not for ROM |
| Shape (P0.3) | Z-score each 101-pt curve; Pearson + DTW separately |
| CRP (P0.6) | Hilbert analytic phase; circular `mean cos(ΔCRP)` + DTW on unwrap |

**Robust (Phase 3) vs exploratory:** a small *p*-value without FDR, LOSO, and subject consistency is not a signature.

**Robust (Phase 6) trajectory region:** predefined primary channel, cluster permutation + FDR, medium+ effect, consistency, LOSO sign agreement, bootstrap CI excluding 0, contiguous phase span.

**Similarity P0 “surviving” claim:** post-residual perm *p* ≤ 0.05 on the similarity side of the null, LOSO pass where defined, and FDR survivors when a multi-test family was pre-registered — then still requires an **independent cohort**.

---

## 9. Where to read results

| Phase / P0 | Report | Certification / lock file |
|---|---|---|
| 0 | `results/phase0/audit_report.md` | in that report |
| 1 | `results/phase1/phase1_report.md` | PASS in report |
| 2 | `results/phase2/phase2_report.md` | `phase2_certification.md` |
| 3 | `results/phase3/phase3_report.md` | `phase3_certification.md` |
| 4 | `results/phase4/phase4_report.md` | `phase4_certification.md` |
| 5 | `results/phase5/phase5_report.md` | `phase5_certification.md` |
| 6 | `results/phase6/phase6_report.md` | `phase6_certification.md` |
| P0.1 | `results/similarity/p01_deviation/p01_report.md` | — |
| P0.2 | `results/similarity/p02_abnormality/p02_report.md` | `preregistered_features.json` |
| P0.3 | `results/similarity/p03_shape/p03_report.md` | `preregistered_curves.json` |
| P0.4 | `results/similarity/p04_event_phases/p04_report.md` | `preregistered_phases.json` |
| P0.6 | `results/similarity/p06_coordination/p06_report.md` | `preregistered_pairs.json` |
| P0.1 MDE | `results/similarity/power_analysis/mde_report.md` | post-hoc; does not alter frozen P0 |
| P0 family | `results/similarity/p0_synthesis.md` | decision gate + P1 stop |

Useful tables:

- Phase 2: `subject_features.parquet`, `feature_catalog.json`
- Phase 3: `candidate_signature.csv` (exploratory ranks), `statistics/multiple_testing.csv`
- Phase 4: `phenotype_assignments.csv` (no victim column on the assignment table)
- Phase 5: `similarity/within_victim_similarity.csv`
- Phase 6: `candidate_trajectory_regions.csv` (classifications ROBUST / EXPLORATORY / UNSUPPORTED)
- P0.1: `cosine_matrix.csv`, `subject_alignment.csv`
- P0.2: `exceedance_matrix.csv`, `feature_coexceedance_residualized.csv`
- P0.3: `per_curve_similarity_residualized.csv`
- P0.4: `cell_results_residualized.csv`, `window_multivariate_residualized.csv`
- P0.6: `per_pair_similarity_residualized.csv`

---

## 10. Limitations (read before citing)

1. **n = 31** (17 vs 14) is small. A P0.1 power simulation on the residualized 27-D cloud had **80% power only for a shared deviation direction of magnitude ≥ 0.73×** a typical control’s residual `||d_i||` (expected cosine ≈ **0.30**); the observed cosine **0.052** is well below that MDE, so this null is unsurprising given the design. Absence of evidence is not proof that no gait difference exists in a larger population.
2. Victimization is a **survey label**, heterogeneous (in-person / online / both / Nd), not a controlled exposure.
3. Gait was captured in a **lab Plug-in Gait** protocol, not daily walking.
4. **S15 height** (~141 cm) and low cycle counts (S19, S30) affect some summaries.
5. Coordinate axes are **not** anatomically named.
6. Phase 4’s 4-person outgroup should not be named a clinical “victim phenotype.”
7. A future classifier on these same 31 people would not independently validate anything discovered here.
8. Similarity P0 exhausts several *complementary* shared-pattern constructs; high absolute CRP circular similarity is **normal gait coordination**, not a victim finding, when it does not exceed the subject-label null.
9. Phase 1 core has pelvis **markers**, not PelvisAngles; P0.3/P0.4 used LASI/RASI as documented proxies. ISw/MSw/TSw were **not** interpolated for P0.4.

---

## 11. What this project is not

- Not a diagnostic tool  
- Not evidence of causation  
- Not a claim that “gait identifies victims”  
- Not a license to pool 880 cycles as *n*  
- Not Phase 7 (supervised prediction)  
- Not Similarity P1 (Wasserstein / RV / soft-DTW / common subspace) — **stopped after P0 nulls**

If you extend the work: keep the subject as the unit, freeze preprocessing before looking at labels for unsupervised steps, pre-register any new feature/curve/pair list before testing, and treat any new “signature” as a hypothesis for **new subjects**, not a result to be tuned on this cohort until it appears.
