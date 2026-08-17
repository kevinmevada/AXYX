"""Phase 2 certification. Read-only checks against tables + source. No labels used."""

from __future__ import annotations

import ast
import json
import math
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from .aggregation.subject import aggregate_subjects
from .catalog import CORE_GAIT_SIGNALS
from .features.anatomy import BILATERAL_PAIRS, SIGNAL_ANATOMY
from .features.base import PHASE_BINS, SGOLAY_POLY, SGOLAY_WINDOW
from .features.context import ID_COLUMNS, LABEL_COLUMNS, CycleRecord
from .features.kinematic import extract as kin_extract
from .features.phase import extract as phase_extract
from .features.registry import all_specs, cycle_specs, subject_extra_specs

FORBIDDEN_AXIS_LABELS = re.compile(
    r"(?<![A-Za-z])(AP|ML|VT|anterior|posterior|medial|lateral|vertical|horizontal)(?![A-Za-z])",
    re.I,
)
LABEL_TOKENS = ("victimized", "victim_type", "cyber_bullied", "VICTIMIZED")
FEATURE_SRC = Path(__file__).resolve().parent / "features"
AGG_SRC = Path(__file__).resolve().parent / "aggregation"
ALLOWED_UNITS = {
    "deg",
    "mm",
    "s",
    "pct_cycle",
    "deg_per_s",
    "deg_per_s2",
    "mm_per_s3_sq",
    "deg_per_s3_sq",
    "corr",
    "si_pct",
    "ratio",
    "count",
    "source",
    "mixed",
}
SUBJECT_META = {"subject_id", "n_cycles", "n_left_cycles", "n_right_cycles"}
AGG_SUFFIXES = ("median", "mean", "std", "cv", "n")


@dataclass
class Check:
    name: str
    status: str  # PASS | WARNING | FAIL
    detail: str


def _status(checks: list[Check]) -> str:
    if any(c.status == "FAIL" for c in checks):
        return "FAIL"
    if any(c.status == "WARNING" for c in checks):
        return "PASS WITH WARNINGS"
    return "PASS"


def _scan_py_for_labels(root: Path) -> list[str]:
    hits = []
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value in LABEL_COLUMNS or node.value in LABEL_TOKENS:
                    # Allow the denylist constants themselves.
                    if path.name == "context.py" and node.value in LABEL_COLUMNS:
                        continue
                    hits.append(f"{path.name}: {node.value!r}")
    return hits


def certify_phase2(project_root: Path) -> dict:
    checks: list[Check] = []
    cycle_path = project_root / "results" / "phase2" / "cycle_features.parquet"
    subject_path = project_root / "results" / "phase2" / "subject_features.parquet"
    catalog_path = project_root / "results" / "phase2" / "feature_catalog.json"
    cycle_df = pd.read_parquet(cycle_path)
    subject_df = pd.read_parquet(subject_path)
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

    cycle_feat_cols = [c for c in cycle_df.columns if c not in ID_COLUMNS]
    specs = all_specs()
    cycle_sp = cycle_specs()
    extra_sp = subject_extra_specs()
    spec_by_name = {s.name: s for s in specs}

    # --- labels in tables ---
    leaked_cycle = [c for c in cycle_df.columns if c in LABEL_COLUMNS or "victim" in c.lower()]
    leaked_subj = [c for c in subject_df.columns if c in LABEL_COLUMNS or "victim" in c.lower()]
    checks.append(
        Check(
            "no_label_leakage_tables",
            "PASS" if not leaked_cycle and not leaked_subj else "FAIL",
            f"cycle={leaked_cycle or 'none'}; subject={leaked_subj or 'none'}",
        )
    )

    # --- labels in calculation source (features/ + aggregation/) ---
    src_hits = _scan_py_for_labels(FEATURE_SRC) + _scan_py_for_labels(AGG_SRC)
    # engine.py imports LABEL_COLUMNS only to raise on leak — allow that file's import usage
    checks.append(
        Check(
            "no_labels_in_feature_calculation",
            "PASS" if not src_hits else "FAIL",
            "no victimization tokens in features/ or aggregation/" if not src_hits else "; ".join(src_hits),
        )
    )
    checks.append(
        Check(
            "catalog_labels_used_false",
            "PASS" if catalog.get("labels_used") is False else "FAIL",
            f"catalog.labels_used={catalog.get('labels_used')}",
        )
    )

    # --- imputation documentation ---
    nan_doc = (catalog.get("smoothing") or {}).get("nan_handling") or {}
    has_drop = "dropped" in str(nan_doc.get("rom_min_max_mean", "")).lower() or "finite" in str(nan_doc).lower()
    has_interp = "interpolat" in str(nan_doc.get("derivatives", "")).lower()
    sg_src = (FEATURE_SRC / "base.py").read_text(encoding="utf-8")
    uses_interp = "np.interp" in sg_src and "savgol_filter" in sg_src
    if uses_interp and has_interp and has_drop:
        imp_status, imp_detail = "PASS", "ROM uses finite-only drop; derivative path interpolates NaNs and is documented in the catalog"
    elif uses_interp and not has_interp:
        imp_status, imp_detail = "FAIL", "Savitzky-Golay path interpolates NaNs but catalog does not document it"
    else:
        imp_status, imp_detail = "PASS", "no undocumented imputation found"
    checks.append(Check("no_silent_imputation", imp_status, imp_detail))

    # --- catalog completeness ---
    missing_meta = []
    bad_units = []
    inherit_units = []
    bad_source = []
    axis_mislabel = []
    valid_sources = set(CORE_GAIT_SIGNALS) | {"events"} | set(cycle_feat_cols)
    for spec in specs:
        if not spec.anatomical_region or not spec.related_anatomy or not spec.side:
            missing_meta.append(spec.name)
        if spec.unit not in ALLOWED_UNITS:
            bad_units.append(f"{spec.name}={spec.unit}")
        if spec.unit in {"source", "mixed"}:
            inherit_units.append(spec.name)
        srcs = [p.strip() for p in spec.source_signal.split("|")]
        for src in srcs:
            if src not in valid_sources and src not in SIGNAL_ANATOMY and src not in cycle_feat_cols:
                # coordination uses Signal|Signal; variability uses cycle feature names
                if src not in spec_by_name and src not in cycle_feat_cols:
                    bad_source.append(f"{spec.name}->{src}")
        blob = " ".join([spec.name, spec.description, spec.unit, spec.phase])
        # allow the certification-note wording in catalog coordinates, not in feature names
        if FORBIDDEN_AXIS_LABELS.search(spec.name) or (
            FORBIDDEN_AXIS_LABELS.search(spec.description) and "unverified" not in spec.description.lower()
            and "not certified" not in spec.description.lower()
        ):
            axis_mislabel.append(spec.name)

    checks.append(
        Check(
            "anatomical_metadata",
            "PASS" if not missing_meta else "FAIL",
            "all specs have region/side/related_anatomy" if not missing_meta else f"missing: {missing_meta[:8]}",
        )
    )
    checks.append(
        Check(
            "units_allowed",
            "PASS" if not bad_units else "FAIL",
            "all units in controlled vocabulary" if not bad_units else str(bad_units[:8]),
        )
    )
    checks.append(
        Check(
            "units_inherited_flagged",
            "WARNING" if inherit_units else "PASS",
            f"{len(inherit_units)} specs use unit='source' or 'mixed' (inherit from source feature)"
            if inherit_units
            else "no inherited placeholder units",
        )
    )
    checks.append(
        Check(
            "source_signal_valid",
            "PASS" if not bad_source else "FAIL",
            "all source_signal values resolve to core signals, events, or cycle features"
            if not bad_source
            else str(bad_source[:10]),
        )
    )
    checks.append(
        Check(
            "axes_not_anatomical",
            "PASS" if not axis_mislabel else "FAIL",
            "feature names/descriptions use ax1/ax2/ax3, not AP/ML/vertical" if not axis_mislabel else str(axis_mislabel[:8]),
        )
    )
    coord_note = str((catalog.get("coordinates") or {}).get("note", ""))
    checks.append(
        Check(
            "catalog_coordinate_note",
            "PASS" if "ax" in coord_note.lower() or "not certified" in coord_note.lower() else "FAIL",
            coord_note or "missing",
        )
    )

    # --- reconcile 714 / 805 / 3665 ---
    n_cycle_specs = len(cycle_sp)
    n_extra = len(extra_sp)
    n_catalog = len(specs)
    n_cycle_cols = len(cycle_feat_cols)
    n_subj_cols = len(subject_df.columns)
    expected_subj = len(SUBJECT_META) + n_cycle_cols * len(AGG_SUFFIXES) + n_extra
    spec_names = {s.name for s in cycle_sp}
    col_set = set(cycle_feat_cols)
    checks.append(
        Check(
            "cycle_catalog_vs_table",
            "PASS" if spec_names == col_set else "FAIL",
            f"catalog {n_cycle_specs} vs table {n_cycle_cols}; "
            f"only_catalog={sorted(spec_names - col_set)[:5]}; only_table={sorted(col_set - spec_names)[:5]}",
        )
    )
    checks.append(
        Check(
            "catalog_805_reconcile",
            "PASS" if n_catalog == n_cycle_specs + n_extra else "FAIL",
            f"all_specs={n_catalog} cycle={n_cycle_specs} extra={n_extra} (expected extra symmetry+variability)",
        )
    )
    untraced = []
    for col in subject_df.columns:
        if col in SUBJECT_META:
            continue
        if "__" in col:
            base, suf = col.rsplit("__", 1)
            if suf in AGG_SUFFIXES and base in col_set:
                continue
            untraced.append(col)
            continue
        if col in {s.name for s in extra_sp}:
            continue
        untraced.append(col)
    checks.append(
        Check(
            "subject_columns_traced",
            "PASS" if not untraced and n_subj_cols == expected_subj else "FAIL",
            f"subject_cols={n_subj_cols} expected={expected_subj} untraced={untraced[:8] or 'none'}",
        )
    )

    # --- Savitzky-Golay ---
    sm = catalog.get("smoothing") or {}
    sg_ok = (
        sm.get("derivative_filter") == "savitzky_golay"
        and int(sm.get("window", -1)) == SGOLAY_WINDOW
        and int(sm.get("polyorder", -1)) == SGOLAY_POLY
        and f"savgol_filter(filled, {SGOLAY_WINDOW}, {SGOLAY_POLY}" in sg_src.replace(" ", "")
        or f"savgol_filter(filled, SGOLAY_WINDOW, SGOLAY_POLY" in sg_src
    )
    checks.append(
        Check(
            "savitzky_golay_documented",
            "PASS" if sm.get("window") == SGOLAY_WINDOW and sm.get("polyorder") == SGOLAY_POLY and "savgol_filter" in sg_src else "FAIL",
            f"window={sm.get('window')} poly={sm.get('polyorder')} constants={SGOLAY_WINDOW}/{SGOLAY_POLY}",
        )
    )

    # --- phase bins ---
    expected_bins = tuple((i, i + 10) for i in range(0, 100, 10))
    phase_names = [c for c in cycle_feat_cols if "_phase_" in c]
    missing_bins = []
    for lo, hi in expected_bins:
        tag = f"_phase_{lo}_{hi}_"
        if not any(tag in n for n in phase_names):
            missing_bins.append(f"{lo}_{hi}")
    # synthetic ramp: 0..100
    ramp = np.linspace(0, 100, 101)
    rec = CycleRecord(
        cycle_id="CERT",
        subject_id="SX",
        session_id="WU01",
        trial_id="SX/WU01",
        side="L",
        start_frame=0,
        end_frame=100,
        duration_seconds=1.0,
        sampling_rate_hz=100,
        ipsilateral_foot_off_frame=60,
        opposite_contact_frame=50,
        opposite_foot_off_frame=10,
        mid_stance_frame=30,
        signals={"LKneeAngles": np.column_stack([ramp, ramp, ramp])},
    )
    ph = phase_extract(rec)
    # [0,10) indices 0-9 mean 4.5; [90,100] indices 90-100 mean 95
    m0 = ph.get("LKneeAngles_ax1_phase_0_10_mean", float("nan"))
    m9 = ph.get("LKneeAngles_ax1_phase_90_100_mean", float("nan"))
    phase_math = abs(m0 - 4.5) < 1e-9 and abs(m9 - 95.0) < 1e-9
    checks.append(
        Check(
            "phase_bins_0_100",
            "PASS" if PHASE_BINS == expected_bins and not missing_bins and phase_math else "FAIL",
            f"bins={PHASE_BINS}; missing_names={missing_bins or 'none'}; "
            f"ramp 0-10 mean={m0} (expect 4.5); 90-100 mean={m9} (expect 95)",
        )
    )

    # --- aggregation math + isolation ---
    probe = "LKneeAngles_ax1_rom"
    sid = "S14"
    part = cycle_df.loc[cycle_df["subject_id"] == sid, probe].to_numpy(dtype=float)
    finite = part[np.isfinite(part)]
    exp_med = float(np.median(finite))
    exp_mean = float(np.mean(finite))
    exp_std = float(np.std(finite, ddof=1))
    exp_cv = exp_std / abs(exp_mean)
    row = subject_df.loc[subject_df["subject_id"] == sid].iloc[0]
    math_ok = (
        abs(row[f"{probe}__median"] - exp_med) < 1e-9
        and abs(row[f"{probe}__mean"] - exp_mean) < 1e-9
        and abs(row[f"{probe}__std"] - exp_std) < 1e-9
        and abs(row[f"{probe}__cv"] - exp_cv) < 1e-9
        and int(row[f"{probe}__n"]) == len(finite)
        and int(row["n_cycles"]) == int((cycle_df["subject_id"] == sid).sum())
    )
    checks.append(
        Check(
            "within_subject_median_mean_sd_cv",
            "PASS" if math_ok else "FAIL",
            f"{sid} {probe} median={row[f'{probe}__median']} vs recomputed {exp_med}",
        )
    )

    without = cycle_df[cycle_df["subject_id"] != "S2"]
    alt = aggregate_subjects(without)
    s3_full = float(subject_df.loc[subject_df["subject_id"] == "S3", f"{probe}__median"].iloc[0])
    s3_wo = float(alt.loc[alt["subject_id"] == "S3", f"{probe}__median"].iloc[0])
    checks.append(
        Check(
            "no_cross_subject_influence",
            "PASS" if abs(s3_full - s3_wo) < 1e-12 else "FAIL",
            f"S3 {probe} median with all subjects={s3_full}; after dropping S2 cycles={s3_wo}",
        )
    )

    # --- symmetry pairing ---
    left, right, _ = ("LKneeAngles", "RKneeAngles", "knee")
    s14c = cycle_df[cycle_df["subject_id"] == sid]
    lmed = float(s14c.loc[s14c["side"] == "L", f"{left}_ax1_rom"].median())
    rmed = float(s14c.loc[s14c["side"] == "R", f"{right}_ax1_rom"].median())
    exp_abs = abs(lmed - rmed)
    got_abs = float(row["sym_KneeAngles_ax1_rom_absdiff"])
    # wrong pairing would use L vs R on mixed sides
    wrong = abs(float(s14c[f"{left}_ax1_rom"].median()) - float(s14c[f"{right}_ax1_rom"].median()))
    checks.append(
        Check(
            "symmetry_ipsilateral_pairing",
            "PASS" if abs(got_abs - exp_abs) < 1e-9 else "FAIL",
            f"S14 |L-cycle LKnee - R-cycle RKnee|={exp_abs}; stored={got_abs}; "
            f"same-window-all-cycles |L-R|={wrong} (must not be the stored value unless equal)",
        )
    )

    # --- determinism ---
    knee = np.linspace(10, 50, 101)
    rec2 = CycleRecord(
        cycle_id="D",
        subject_id="SX",
        session_id="WU01",
        trial_id="SX/WU01",
        side="L",
        start_frame=0,
        end_frame=100,
        duration_seconds=1.0,
        sampling_rate_hz=100,
        ipsilateral_foot_off_frame=60,
        opposite_contact_frame=50,
        opposite_foot_off_frame=10,
        mid_stance_frame=30,
        signals={"LKneeAngles": np.column_stack([knee, knee, knee])},
    )
    a = kin_extract(rec2)
    b = kin_extract(rec2)
    det_ok = a.keys() == b.keys() and all(
        (math.isnan(a[k]) and math.isnan(b[k])) or a[k] == b[k] for k in a
    )
    checks.append(Check("deterministic_extract", "PASS" if det_ok else "FAIL", "repeat kinematic extract identical"))

    counts = {
        "cycle_rows": int(len(cycle_df)),
        "cycle_feature_columns": n_cycle_cols,
        "subject_rows": int(len(subject_df)),
        "subject_columns": n_subj_cols,
        "catalog_entries": n_catalog,
        "cycle_specs": n_cycle_specs,
        "subject_extra_specs": n_extra,
        "expected_subject_columns": expected_subj,
    }
    payload = {
        "generated": date.today().isoformat(),
        "status": _status(checks),
        "counts": counts,
        "checks": [asdict(c) for c in checks],
    }
    return payload


def write_certification(project_root: Path, payload: dict) -> dict[str, Path]:
    out = project_root / "results" / "phase2"
    json_path = out / "phase2_certification.json"
    md_path = out / "phase2_certification.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = [
        "# Phase 2 certification",
        "",
        f"Status: **{payload['status']}**",
        "",
        f"Generated: {payload['generated']}",
        "",
        "## Counts",
        "",
    ]
    for k, v in payload["counts"].items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Checks", ""]
    for c in payload["checks"]:
        lines.append(f"- `{c['name']}`: **{c['status']}** — {c['detail']}")
    lines.append("")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": json_path, "report": md_path}


def render_cert_console(payload: dict) -> str:
    lines = [
        "=" * 60,
        "AXYS ML - PHASE 2 CERTIFICATION",
        "=" * 60,
        "",
    ]
    for k, v in payload["counts"].items():
        lines.append(f"{k:<28} {v}")
    lines += ["", "-" * 60, "CHECKS", "-" * 60, ""]
    for c in payload["checks"]:
        lines.append(f"{c['status']:<22} {c['name']}")
        lines.append(f"{'':22} {c['detail']}")
        lines.append("")
    lines += ["-" * 60, "FINAL STATUS", "-" * 60, "", payload["status"], ""]
    return "\n".join(lines)
