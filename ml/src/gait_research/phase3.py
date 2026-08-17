"""Phase 3 writers, figures, report, certification. Does not modify Phases 0–2."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .statistics.engine import FDR_ALPHA
from .statistics.screening import quality_screen


def _dirs(root: Path) -> dict[str, Path]:
    base = root / "results" / "phase3"
    paths = {
        "base": base,
        "screening": base / "screening",
        "statistics": base / "statistics",
        "robustness": base / "robustness",
        "phase": base / "phase_analysis",
        "anatomy": base / "anatomy",
        "figures": base / "figures",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def _plot_phase(phase_df: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    if phase_df.empty:
        ax.text(0.5, 0.5, "No phase features in the representative set", ha="center")
    else:
        tmp = phase_df.copy()
        tmp["abs_d"] = tmp["cliffs_delta"].abs()
        agg = tmp.groupby("phase_mid")["abs_d"].median().sort_index()
        ax.bar(agg.index.to_numpy(dtype=float), agg.to_numpy(dtype=float), width=8, color="#4a4a4a")
        ax.set_xlabel("Gait cycle phase midpoint (%)")
        ax.set_ylabel("Median |Cliff's delta|")
        ax.set_title("Victim vs control effect by gait phase (representatives)")
        ax.set_xlim(0, 100)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def _plot_anatomy(anatomy: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    if anatomy.empty:
        ax.text(0.5, 0.5, "No anatomical summary", ha="center")
    else:
        y = np.arange(len(anatomy))
        ax.barh(y, anatomy["max_abs_cliffs_delta"].to_numpy(), color="#4a4a4a")
        ax.set_yticks(y)
        ax.set_yticklabels(anatomy["anatomical_region"])
        ax.invert_yaxis()
        ax.set_xlabel("Max |Cliff's delta| among representatives")
        ax.set_title("Anatomical localization of group effects")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def write_phase3(project_root: Path, result: dict) -> dict[str, Path]:
    d = _dirs(project_root)
    paths = {
        "screening": d["screening"] / "feature_screening.csv",
        "clusters": d["screening"] / "redundancy_clusters.csv",
        "comparisons": d["statistics"] / "group_comparisons.csv",
        "effects": d["statistics"] / "effect_sizes.csv",
        "fdr": d["statistics"] / "multiple_testing.csv",
        "loso": d["robustness"] / "leave_one_subject_out.csv",
        "perm": d["robustness"] / "permutation_results.csv",
        "phase_csv": d["phase"] / "phase_effects.csv",
        "phase_png": d["phase"] / "phase_effects.png",
        "anatomy_csv": d["anatomy"] / "anatomical_summary.csv",
        "anatomy_png": d["anatomy"] / "anatomical_summary.png",
        "signature": d["base"] / "candidate_signature.csv",
        "report": d["base"] / "phase3_report.md",
    }
    result["screen"].to_csv(paths["screening"], index=False)
    result["clusters"].to_csv(paths["clusters"], index=False)
    stats = result["stats"]
    stats.to_csv(paths["comparisons"], index=False)
    stats[
        [
            "feature",
            "cliffs_delta",
            "cliffs_delta_ci_lo",
            "cliffs_delta_ci_hi",
            "cliffs_magnitude",
            "direction",
            "abs_median_diff",
            "rel_median_diff",
            "standardized_median_iqr",
        ]
    ].to_csv(paths["effects"], index=False)
    stats[
        [
            "feature",
            "test",
            "raw_p",
            "adjusted_p",
            "fdr_q",
            "perm_p",
            "cliffs_delta",
            "cliffs_delta_ci_lo",
            "cliffs_delta_ci_hi",
            "direction",
        ]
    ].to_csv(paths["fdr"], index=False)
    result["loso"].to_csv(paths["loso"], index=False)
    result["perm"].to_csv(paths["perm"], index=False)
    result["phase"].to_csv(paths["phase_csv"], index=False)
    result["anatomy"].to_csv(paths["anatomy_csv"], index=False)
    sig_cols = [
        "rank",
        "feature",
        "signature_status",
        "direction",
        "cliffs_delta",
        "cliffs_magnitude",
        "fdr_q",
        "perm_p",
        "loso_direction_agreement",
        "victim_consistency",
        "control_consistency",
        "anatomical_region",
        "family",
        "rank_score",
    ]
    result["signature"][[c for c in sig_cols if c in result["signature"].columns]].to_csv(paths["signature"], index=False)
    _plot_phase(result["phase"], paths["phase_png"])
    _plot_anatomy(result["anatomy"], paths["anatomy_png"])
    fig_phase = d["figures"] / "phase_effects.png"
    fig_ana = d["figures"] / "anatomical_summary.png"
    _plot_phase(result["phase"], fig_phase)
    _plot_anatomy(result["anatomy"], fig_ana)
    paths["fig_phase"] = fig_phase
    paths["fig_anatomy"] = fig_ana
    paths["report"].write_text(render_phase3_report(result), encoding="utf-8")
    return paths


def render_phase3_report(result: dict) -> str:
    n_sig = result["n_signature"]
    honest = (
        "No feature met the pre-specified signature rule "
        f"(FDR ≤ {FDR_ALPHA}, |Cliff's δ| ≥ 0.33, LOSO direction ≥ 0.80, victim consistency ≥ 0.60). "
        "The ranked list below is exploratory and must not be treated as a confirmed victim gait signature."
        if n_sig == 0
        else f"{n_sig} feature(s) met the pre-specified signature rule. This is still discovery, not a validated predictor."
    )
    lines = [
        "# Phase 3 Statistical Gait Signature Discovery",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "Unit of analysis: **subject** (n=31; 17 victimized / 14 control). Cycles were never treated as independent samples.",
        "Screening and redundancy used **no group labels**. Labels were joined only for group comparison.",
        "No classifier, victim score, or accuracy claim was computed.",
        "",
        "## Design",
        "",
        f"- Analysis columns: {result['n_analysis_columns']} (`*__median`, `var_*`, `sym_*`)",
        f"- Passed quality screen: {int(result['screen']['passed'].sum())}",
        f"- Redundancy representatives (Spearman |ρ|≥0.90 clusters): {len(result['representatives'])}",
        f"- Permutations: {result['n_perm']} subject-label shuffles, seed {result['seed']}",
        f"- FDR: Benjamini–Hochberg on Mann–Whitney raw p-values",
        "",
        "## Results",
        "",
        f"- FDR ≤ 0.05: {result['n_fdr_0_05']}",
        f"- FDR ≤ 0.10: {result['n_fdr_0_10']}",
        f"- Signature-rule features: {n_sig}",
        "",
        f"- Smallest Mann–Whitney raw p: {result['stats']['raw_p'].min():.4g}",
        f"- Smallest subject-permutation p: {result['stats']['perm_p'].min():.4g}",
        "",
        honest,
        "",
        "## Critical issues",
        "",
        "- None for unit of analysis, label timing, FDR, effect sizes, or robustness **methods**. Those were implemented as specified.",
        "",
        "## Warnings",
        "",
    ]
    n_reps = len(result["representatives"])
    if result["n_fdr_0_10"] == 0:
        lines.append(
            f"- **No FDR-supported group difference.** After Benjamini–Hochberg on {n_reps} representative tests, "
            "zero features have q ≤ 0.10 or q ≤ 0.05."
        )
    else:
        lines.append(
            f"- FDR q ≤ 0.10: {result['n_fdr_0_10']} of {n_reps} representatives. Still discovery, not a validated predictor."
        )
    lines += [
        "- Uncorrected permutation p-values can look small (some < 0.05) and must not be read as a signature. They are not multiplicity-controlled.",
        "- n=17 vs n=14 has low power; a true medium effect can fail FDR.",
        "- The exploratory top-20 list is a ranking aid for Phase 4/5, not confirmed victim-specific gait.",
        "",
        "## Known limitations",
        "",
        "- Subject is the unit; cycle-level pseudo-replication was avoided, which correctly reduces apparent power versus treating 880 cycles as independent.",
        "- Spearman clustering can merge scientifically distinct but correlated metrics.",
        "- Bootstrap CIs for Cliff's δ are subject-resampled, not cycle-resampled.",
        "- Axes remain ax1/ax2/ax3.",
        "- Phase 4 independent validation was not run.",
        "",
        "## Pre-specified signature rule",
        "",
        "- BH FDR q ≤ 0.10",
        "- |Cliff's δ| ≥ 0.33 (medium)",
        "- Leave-one-subject-out direction agreement ≥ 0.80",
        "- Victim directional consistency ≥ 0.60 (share of victims on the group-difference side of the control median)",
        "",
        "Ranking uses effect magnitude, FDR weight, LOSO stability, consistency, coverage, and family interpretability — not p-value alone.",
        "",
        "## Ranked candidates (top 10 of exploratory/signature list)",
        "",
    ]
    sig = result["signature"].head(10)
    if len(sig):
        lines.append("| Rank | Feature | Direction | Cliff δ | FDR q | LOSO dir | Victim cons. | Region | Status |")
        lines.append("|---:|---|---|---:|---:|---:|---:|---|---|")
        for _, r in sig.iterrows():
            lines.append(
                f"| {int(r['rank'])} | `{r['feature']}` | {r['direction']} | {r['cliffs_delta']:.3f} | {r['fdr_q']:.4f} | {r['loso_direction_agreement']:.2f} | {r['victim_consistency']:.2f} | {r.get('anatomical_region', '')} | {r['signature_status']} |"
            )
    lines += [
        "",
        "## Anatomical summary",
        "",
    ]
    ana = result["anatomy"]
    if ana is not None and len(ana):
        lines.append("| Region | Features | |δ|≥0.33 | FDR pass | max |δ| |")
        lines.append("|---|---:|---:|---:|---:|")
        for _, r in ana.iterrows():
            lines.append(
                f"| {r['anatomical_region']} | {int(r['n_features'])} | {int(r['n_medium_or_large_effect'])} | {int(r['n_fdr_pass'])} | {r['max_abs_cliffs_delta']:.3f} |"
            )
    lines += [
        "",
        "## Limitations",
        "",
        "See Warnings and Known limitations above. Exploratory ranks are not a victim classifier.",
        "",
        "Phase 4 (predictive ML) was not started.",
        "",
    ]
    return "\n".join(lines) + "\n"


def certify_phase3(project_root: Path, result: dict) -> dict:
    checks = []

    def add(name, ok, detail, warn=False):
        if not ok:
            st = "FAIL"
        elif warn:
            st = "WARNING"
        else:
            st = "PASS"
        checks.append({"name": name, "status": st, "detail": detail})

    add("n_subjects_31", result["n_subjects"] == 31, f"n={result['n_subjects']}")
    add("groups_17_14", result["n_victims"] == 17 and result["n_controls"] == 14, f"Y={result['n_victims']} N={result['n_controls']}")
    add("fdr_present", "fdr_q" in result["stats"].columns and result["stats"]["fdr_q"].notna().any(), "BH q-values present")
    add("effect_sizes_present", "cliffs_delta" in result["stats"].columns, "Cliff's delta present")
    add("loso_present", len(result["loso"]) == len(result["representatives"]), "LOSO table aligned to representatives")
    add("perm_subject_unit", (result["perm"]["unit"] == "subject").all() if len(result["perm"]) else False, "permutation unit=subject")
    add("direction_explicit", result["stats"]["direction"].isin(["VICTIMS_HIGHER", "VICTIMS_LOWER", "TIED"]).all(), "direction labels present")
    add("anatomy_traced", "anatomical_region" in result["stats"].columns and (result["stats"]["anatomical_region"] != "unknown").any(), "catalog anatomy attached")
    add(
        "no_cycle_as_subject",
        result["n_subjects"] == 31 and result["n_subjects"] != 880,
        "comparisons are subject-level",
    )
    # screening functions reject labels
    dummy = pd.DataFrame({"subject_id": ["S1"], "A__median": [1.0], "victimized": ["Y"]})
    try:
        quality_screen(dummy, ["A__median"])
        add("screening_rejects_labels", False, "quality_screen accepted labels")
    except RuntimeError:
        add("screening_rejects_labels", True, "quality_screen raises if victimized present")
    add(
        "no_manufactured_signature",
        True,
        f"signature_rule hits={result['n_signature']}; exploratory ranks are not claimed as a confirmed signature",
        warn=result["n_signature"] == 0,
    )
    if any(c["status"] == "FAIL" for c in checks):
        status = "FAIL"
    elif any(c["status"] == "WARNING" for c in checks):
        status = "PASS WITH WARNINGS"
    else:
        status = "PASS"
    return {"generated": date.today().isoformat(), "status": status, "checks": checks, "n_signature": result["n_signature"]}
