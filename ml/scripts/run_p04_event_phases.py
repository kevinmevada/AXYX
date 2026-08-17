"""P0.4 runner: event-localized phase-window similarity.

Does not modify Phases 0–6. Writes results/similarity/p04_event_phases/.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gait_research.similarity.deviation import residualize_columns  # noqa: E402
from gait_research.similarity.event_phases import run_event_phase_battery  # noqa: E402
from gait_research.similarity.load import load_covariates, load_event_phase_features  # noqa: E402

SEED = 20260813


def _dirs(root: Path) -> Path:
    out = root / "results" / "similarity" / "p04_event_phases"
    (out / "figures").mkdir(parents=True, exist_ok=True)
    return out


def _heatmap(cell_df: pd.DataFrame, test_type: str, value: str, path: Path, title: str) -> None:
    sub = cell_df[cell_df["test_type"] == test_type].copy()
    # average over aggregations for display grid phase × curve
    if value == "neglog10_p":
        sub["val"] = -np.log10(np.clip(sub["raw_p"].to_numpy(dtype=float), 1e-16, 1.0))
        agg = sub.groupby(["phase", "curve"], as_index=False)["val"].max()
        cbar = "-log10(raw p) max over mean/rom"
    elif value == "fdr_q":
        sub["val"] = sub["fdr_q"].to_numpy(dtype=float)
        agg = sub.groupby(["phase", "curve"], as_index=False)["val"].min()
        cbar = "min FDR q over mean/rom"
    else:
        sub["val"] = sub["observed"].to_numpy(dtype=float)
        agg = sub.groupby(["phase", "curve"], as_index=False)["val"].mean()
        cbar = "mean observed statistic"
    phases = list(dict.fromkeys(sub["phase"]))
    curves = list(dict.fromkeys(sub["curve"]))
    mat = np.full((len(phases), len(curves)), np.nan)
    for r in agg.itertuples(index=False):
        mat[phases.index(r.phase), curves.index(r.curve)] = r.val
    fig, ax = plt.subplots(figsize=(12, 4.2))
    im = ax.imshow(mat, aspect="auto", cmap="viridis")
    ax.set_yticks(range(len(phases)))
    ax.set_yticklabels(phases, fontsize=8)
    ax.set_xticks(range(len(curves)))
    ax.set_xticklabels([c.replace("__", "_") for c in curves], fontsize=6, rotation=90)
    ax.set_title(title)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label=cbar)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def _write_report(out: Path, raw: dict, resid: dict, n_fdr: int) -> None:
    s = raw["summary"]
    r = resid["summary"]
    decision = (
        "NULL after residualization"
        if r["n_fdr_le_0_10"] == 0
        else "CANDIDATE phase-localized signal (requires independent cohort)"
    )
    w = resid["window_table"]
    win_lines = [
        f"| {row.phase} | {row.deviation_cosine:.4f} | {row.deviation_perm_p:.4g} | {row.deviation_loso_pass} | "
        f"{row.abnormality_jaccard:.4f} | {row.abnormality_perm_p:.4g} | {row.abnormality_loso_pass} |"
        for row in w.itertuples(index=False)
    ]
    text = f"""# P0.4 Event-localized phase-window similarity

Generated: {date.today().isoformat()}

## Question

Is victim similarity localized to specific clinical gait phases that whole-cycle
tests (P0.1–P0.3) dilute into noise?

Unit: **subject** (n=31). Labels shuffled across subjects only.

## Phase audit (pre-registration)

Phase 1 stores IC, opposite FO, mid-stance (Midsvnt), opposite FC, ipsilateral
FO, and next IC for all 880 cycles (100% complete; strict order).

**Reconstructable (used):** loading response, mid-stance, terminal stance,
pre-swing, undivided swing (5 windows).

**Not reconstructable (not estimated):** initial / mid / terminal swing splits
(no feet-adjacent, tibia-vertical, or equivalent events).

Locked in `preregistered_phases.json` before any real test.

## FDR family (stated before running)

**n = {n_fdr}** = 5 phases × 12 P0.3 curves × 2 aggregations (mean, rom) × 2
tests (deviation cosine, abnormality Jaccard). BH-FDR spans this entire family
(not per-window).

## Pre-residual

| Metric | Value |
|---|---|
| FDR family size | {s['n_fdr_family']} |
| Cells with FDR q ≤ 0.10 | {s['n_fdr_le_0_10']} |
| Cells with FDR q ≤ 0.05 | {s['n_fdr_le_0_05']} |
| Min raw perm p | {s['min_perm_p']:.4g} |

## Post-residual (height, mass, mean leg length, cycle duration)

| Metric | Value |
|---|---|
| FDR family size | {r['n_fdr_family']} |
| Cells with FDR q ≤ 0.10 | {r['n_fdr_le_0_10']} |
| Cells with FDR q ≤ 0.05 | {r['n_fdr_le_0_05']} |
| Min raw perm p | {r['min_perm_p']:.4g} |
| Covariates | {', '.join(r['residual_covariates'])} |

### Per-window multivariate (24-D: 12 curves × mean/rom) — LOSO

| Phase | Cosine | Cos p | Cos LOSO | Jaccard | Jac p | Jac LOSO |
|---|---|---|---|---|---|---|
{chr(10).join(win_lines)}

## Decision (P0.4 only)

**{decision}**

Gate: primary evidence is **post-residual** FDR across the full {n_fdr}-cell
family. A defensible phase-localized claim requires ≥1 cell with FDR q ≤ 0.10
after residualization (and supporting window-level LOSO for that phase).

Phases 0–6 were not modified.

## Note on P0.5 / P0.6

P0.5 in the original plan (“confound as shared residual pattern”) is largely
already folded into P0.1–P0.4 via pre/post residualization on height/mass/leg/
cycle duration. Unless you want a dedicated residual-*pattern* similarity test
(victims share the confound-residual direction itself), the natural next step
after P0.4 is **P0.6 CRP/coordination**. Confirm or correct before proceeding.
"""
    (out / "p04_report.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="P0.4 event-phase localized similarity")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--n-perm", type=int, default=9999)
    args = parser.parse_args()
    root = args.root.resolve()
    out = _dirs(root)

    data = load_event_phase_features(root)
    X = data["X"]
    victim = data["victim"]
    names = data["feature_names"]
    phase_ids = data["phase_ids"]
    n_fdr = data["n_fdr_family"]
    print(f"FDR family size (pre-registered): {n_fdr}")
    print(f"Feature matrix: {X.shape}")

    cov, cov_names = load_covariates(root, data["subject_id"])

    print("Stage 1/2: pre-residual battery ...")
    summary, details = run_event_phase_battery(
        X,
        names,
        victim,
        phase_ids,
        representation="event_phase_windows",
        n_perm=args.n_perm,
        seed=SEED,
        show_progress=True,
        progress_desc="raw",
    )
    X_res = residualize_columns(X, cov)
    print("Stage 2/2: post-residual battery ...")
    summary_r, details_r = run_event_phase_battery(
        X_res,
        names,
        victim,
        phase_ids,
        representation="event_phase_windows_residualized",
        n_perm=args.n_perm,
        seed=SEED,
        residualized=True,
        residual_covariates=tuple(cov_names),
        show_progress=True,
        progress_desc="residualized",
    )

    pd.DataFrame([summary.to_dict(), summary_r.to_dict()]).to_csv(out / "summary.csv", index=False)
    details["cell_table"].to_csv(out / "cell_results.csv", index=False)
    details_r["cell_table"].to_csv(out / "cell_results_residualized.csv", index=False)
    details["window_table"].to_csv(out / "window_multivariate.csv", index=False)
    details_r["window_table"].to_csv(out / "window_multivariate_residualized.csv", index=False)
    feat = pd.DataFrame(X, columns=names)
    feat.insert(0, "subject_id", data["subject_id"])
    feat.insert(1, "victimized", np.where(victim, "Y", "N"))
    feat.to_csv(out / "subject_phase_features.csv", index=False)
    (out / "summary.json").write_text(
        json.dumps({"raw": summary.to_dict(), "residualized": summary_r.to_dict()}, indent=2),
        encoding="utf-8",
    )

    _heatmap(
        details["cell_table"],
        "deviation_cosine",
        "neglog10_p",
        out / "figures" / "heatmap_cosine_neglog10p.png",
        "P0.4 deviation cosine −log10(p) by phase × curve",
    )
    _heatmap(
        details["cell_table"],
        "abnormality_jaccard",
        "neglog10_p",
        out / "figures" / "heatmap_jaccard_neglog10p.png",
        "P0.4 abnormality Jaccard −log10(p) by phase × curve",
    )
    _heatmap(
        details_r["cell_table"],
        "deviation_cosine",
        "neglog10_p",
        out / "figures" / "heatmap_cosine_neglog10p_residualized.png",
        "P0.4 deviation cosine −log10(p) (residualized)",
    )
    _heatmap(
        details_r["cell_table"],
        "abnormality_jaccard",
        "neglog10_p",
        out / "figures" / "heatmap_jaccard_neglog10p_residualized.png",
        "P0.4 abnormality Jaccard −log10(p) (residualized)",
    )
    _heatmap(
        details_r["cell_table"],
        "deviation_cosine",
        "fdr_q",
        out / "figures" / "heatmap_cosine_fdr_residualized.png",
        "P0.4 deviation cosine FDR q (residualized)",
    )

    _write_report(
        out,
        {"summary": summary.to_dict(), "window_table": details["window_table"]},
        {"summary": summary_r.to_dict(), "window_table": details_r["window_table"]},
        n_fdr,
    )

    print("=" * 60)
    print("P0.4 EVENT-LOCALIZED PHASE SIMILARITY")
    print("=" * 60)
    print(f"Source             {data['source']}")
    print(f"FDR family         {n_fdr}")
    print("--- pre-residual ---")
    print(f"FDR q<=0.10        {summary.n_fdr_le_0_10}")
    print(f"min raw p          {summary.min_perm_p:.4g}")
    print("--- post-residual ---")
    print(f"FDR q<=0.10        {summary_r.n_fdr_le_0_10}")
    print(f"min raw p          {summary_r.min_perm_p:.4g}")
    print(f"Wrote              {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
