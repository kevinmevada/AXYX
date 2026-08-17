"""Phase 2 orchestration: extract, aggregate, catalog, QA. No victimization labels."""

from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from .aggregation.subject import aggregate_subjects
from .features.base import SGOLAY_POLY, SGOLAY_WINDOW
from .features.context import LABEL_COLUMNS
from .features.engine import extract_cycle_features, load_cycles
from .features.registry import all_specs, cycle_specs, subject_extra_specs


def feature_quality(cycle_df: pd.DataFrame, subject_df: pd.DataFrame, specs) -> pd.DataFrame:
    id_like = {"cycle_id", "subject_id", "session_id", "trial_id", "side", "start_frame", "end_frame", "duration_seconds"}
    cycle_feats = [c for c in cycle_df.columns if c not in id_like]
    n_cycles = len(cycle_df)
    n_subjects = subject_df["subject_id"].nunique() if len(subject_df) else 0
    spec_map = {s.name: s for s in specs}
    rows = []
    for name in cycle_feats:
        x = cycle_df[name]
        n_valid = int(x.notna().sum()) if not np.issubdtype(x.dtype, np.object_) else int(pd.to_numeric(x, errors="coerce").notna().sum())
        # subjects with at least one finite value
        tmp = cycle_df[["subject_id", name]].copy()
        tmp[name] = pd.to_numeric(tmp[name], errors="coerce")
        n_subj = int(tmp.groupby("subject_id")[name].apply(lambda s: s.notna().any()).sum())
        spec = spec_map.get(name)
        rows.append(
            {
                "name": name,
                "level": "cycle",
                "family": spec.family if spec else "unknown",
                "source_signal": spec.source_signal if spec else "",
                "n_valid_cycles": n_valid,
                "n_cycles": n_cycles,
                "missing_fraction_cycles": 1.0 - n_valid / n_cycles if n_cycles else 1.0,
                "n_valid_subjects": n_subj,
                "n_subjects": n_subjects,
                "missing_fraction_subjects": 1.0 - n_subj / n_subjects if n_subjects else 1.0,
            }
        )
    extra = [s.name for s in subject_extra_specs()]
    for name in extra:
        if name not in subject_df.columns:
            continue
        spec = spec_map.get(name)
        x = pd.to_numeric(subject_df[name], errors="coerce")
        n_valid = int(x.notna().sum())
        rows.append(
            {
                "name": name,
                "level": "subject",
                "family": spec.family if spec else "unknown",
                "source_signal": spec.source_signal if spec else "",
                "n_valid_cycles": "",
                "n_cycles": "",
                "missing_fraction_cycles": "",
                "n_valid_subjects": n_valid,
                "n_subjects": n_subjects,
                "missing_fraction_subjects": 1.0 - n_valid / n_subjects if n_subjects else 1.0,
            }
        )
    return pd.DataFrame(rows)


def run_phase2(project_root: Path):
    records = load_cycles(project_root)
    cycle_df = extract_cycle_features(records)
    subject_df = aggregate_subjects(cycle_df)
    specs = all_specs()
    quality = feature_quality(cycle_df, subject_df, specs)
    return {
        "cycle_df": cycle_df,
        "subject_df": subject_df,
        "quality": quality,
        "specs": specs,
        "n_records": len(records),
    }


def write_phase2_outputs(project_root: Path, result: dict) -> dict[str, Path]:
    out = project_root / "results" / "phase2"
    dist = out / "feature_distributions"
    out.mkdir(parents=True, exist_ok=True)
    dist.mkdir(parents=True, exist_ok=True)

    cycle_path = out / "cycle_features.parquet"
    subject_path = out / "subject_features.parquet"
    catalog_path = out / "feature_catalog.json"
    quality_path = out / "feature_quality.csv"
    report_path = out / "phase2_report.md"
    quant_path = dist / "cycle_feature_quantiles.csv"

    result["cycle_df"].to_parquet(cycle_path, index=False)
    result["subject_df"].to_parquet(subject_path, index=False)
    result["quality"].to_csv(quality_path, index=False)

    catalog = {
        "generated": date.today().isoformat(),
        "smoothing": {
            "derivative_filter": "savitzky_golay",
            "window": SGOLAY_WINDOW,
            "polyorder": SGOLAY_POLY,
            "applied_to": "velocity, acceleration, jerk only; ROM/min/max use unsmoothed normalized trajectories",
            "nan_handling": {
                "rom_min_max_mean": "finite samples only; NaNs dropped, not imputed",
                "derivatives": "isolated NaNs linearly interpolated before Savitzky-Golay, then differentiated; documented, identical for all cycles, no labels",
            },
            "group_labels_used": False,
        },
        "coordinates": {
            "axes": ["ax1", "ax2", "ax3"],
            "note": "AP/ML/vertical not certified; spatial features use axis_1/2/3.",
        },
        "aggregation_default": "median",
        "labels_used": False,
        "cycle_features": [s.to_dict() for s in cycle_specs()],
        "subject_extra_features": [s.to_dict() for s in subject_extra_specs()],
    }
    catalog_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")

    id_like = {"cycle_id", "subject_id", "session_id", "trial_id", "side", "start_frame", "end_frame", "duration_seconds"}
    num_cols = [c for c in result["cycle_df"].columns if c not in id_like]
    quant = result["cycle_df"][num_cols].quantile([0.0, 0.25, 0.5, 0.75, 1.0], numeric_only=True).T
    quant.columns = ["min", "q25", "median", "q75", "max"]
    quant.to_csv(quant_path)

    report_path.write_text(render_phase2_report(result), encoding="utf-8")
    return {
        "cycle": cycle_path,
        "subject": subject_path,
        "catalog": catalog_path,
        "quality": quality_path,
        "report": report_path,
        "quantiles": quant_path,
    }


def render_phase2_report(result: dict) -> str:
    cycle_df = result["cycle_df"]
    subject_df = result["subject_df"]
    quality = result["quality"]
    specs = result["specs"]
    families = Counter(s.family for s in specs)
    q_cycle = quality[quality["level"] == "cycle"] if len(quality) else quality
    sufficient = 0
    warnings = 0
    unavailable = 0
    if len(q_cycle):
        sufficient = int((q_cycle["n_valid_subjects"] == q_cycle["n_subjects"]).sum())
        warnings = int(((q_cycle["missing_fraction_cycles"] > 0) & (q_cycle["n_valid_subjects"] > 0)).sum())
        unavailable = int((q_cycle["n_valid_subjects"] == 0).sum())

    leaked = [c for c in LABEL_COLUMNS if c in cycle_df.columns or c in subject_df.columns]
    lines = [
        "# Phase 2 Gait Feature Discovery Engine",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "Victimization labels were **not** used in feature construction or aggregation.",
        "Default subject summary is the **median** across that subject's cycles.",
        "Derivatives use Savitzky-Golay (window 11, poly 3) on the 101-point cycle; ROM/min/max do not.",
        "Spatial axes are `ax1/ax2/ax3` until the lab coordinate convention is certified.",
        "",
        "## Coverage",
        "",
        f"- Cycles: {len(cycle_df)}",
        f"- Subjects: {subject_df['subject_id'].nunique()}",
        f"- Cycle-level feature columns: {len(cycle_df.columns) - 8}",
        f"- Subject-level columns: {len(subject_df.columns)} (each cycle feature × median/mean/std/cv/n, plus symmetry and variability)",
        f"- Catalog entries: {len(specs)}",
        f"- Label columns leaked: {leaked or 'none'}",
        "",
        "Phase 3 should default to `*__median` subject columns unless a dispersion feature is the scientific target.",
        "",
        "## Families (catalog)",
        "",
    ]
    for fam, n in sorted(families.items()):
        lines.append(f"- {fam}: {n}")
    lines += [
        "",
        "## Cycle-level QA",
        "",
        f"- Features with complete subject coverage: {sufficient}",
        f"- Features with some missingness: {warnings}",
        f"- Features unavailable: {unavailable}",
        "",
        "No victim-vs-control tests were run. That is Phase 3.",
        "",
        "## Completion",
        "",
        "- Kinematic, temporal, spatial, phase, coordination, smoothness at cycle level",
        "- Symmetry (ipsilateral-aligned) and variability at subject level",
        "- Feature catalog + anatomy metadata",
        "- Cycle and subject parquet tables",
        "- Feature quality table",
        "",
    ]
    return "\n".join(lines) + "\n"


def render_phase2_console(result: dict) -> str:
    cycle_df = result["cycle_df"]
    subject_df = result["subject_df"]
    families = Counter(s.family for s in result["specs"])
    leaked = [c for c in LABEL_COLUMNS if c in cycle_df.columns or c in subject_df.columns]
    lines = [
        "=" * 60,
        "AXYS ML - PHASE 2 FEATURE ENGINE",
        "=" * 60,
        "",
        f"{'Cycles':<28} {len(cycle_df)}",
        f"{'Subjects':<28} {subject_df['subject_id'].nunique()}",
        f"{'Catalog features':<28} {len(result['specs'])}",
        f"{'Labels used':<28} no",
        f"{'Label leak':<28} {leaked or 'none'}",
        "",
    ]
    for fam, n in sorted(families.items()):
        lines.append(f"{fam:<28} {n}")
    lines += ["", "Status: PASS" if not leaked and len(cycle_df) == result["n_records"] else "Status: FAIL", ""]
    return "\n".join(lines)
