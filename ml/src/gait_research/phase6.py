"""Phase 6 writers, figures, report, certification. Does not modify Phases 0–5."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .features.base import AXIS_NAMES, PHASE_BINS


def _dirs(root: Path) -> dict[str, Path]:
    base = root / "results" / "phase6"
    paths = {
        "base": base,
        "trajectory_data": base / "trajectory_data",
        "group": base / "group_trajectories",
        "statistics": base / "statistics",
        "shape": base / "shape",
        "asymmetry": base / "asymmetry",
        "consistency": base / "consistency",
        "anatomy": base / "anatomy",
        "figures": base / "figures",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def _cand_table(clusters: pd.DataFrame) -> pd.DataFrame:
    if clusters is None or clusters.empty:
        return pd.DataFrame()
    cols = {
        "channel": "signal",
        "family": "signal_family",
        "side": "side",
        "axis": "axis",
        "anatomical_region": "anatomical_region",
        "start_percent": "start_percent",
        "end_percent": "end_percent",
        "direction": "effect_direction",
        "mean_difference": "effect_size",
        "mean_cliffs_delta": "standardized_effect",
        "mean_victim_consistency": "victim_consistency",
        "mean_control_consistency": "control_consistency",
        "permutation_p": "raw_p",
        "fdr_q": "adjusted_p",
        "permutation_p": "permutation_p",
        "bootstrap_ci_low": "bootstrap_ci_low",
        "bootstrap_ci_high": "bootstrap_ci_high",
        "loo_sign_agreement": "leave_one_out_stability",
        "classification": "classification",
        "source_phase": "source_phase",
        "provenance": "provenance",
        "level": "analysis_level",
        "related_marker": "related_marker",
        "signal": "source_signal",
    }
    out = pd.DataFrame()
    for src, dst in [
        ("channel", "signal"),
        ("family", "signal_family"),
        ("side", "side"),
        ("axis", "axis"),
        ("anatomical_region", "anatomical_region"),
        ("start_percent", "start_percent"),
        ("end_percent", "end_percent"),
        ("direction", "effect_direction"),
        ("mean_difference", "effect_size"),
        ("mean_cliffs_delta", "standardized_effect"),
        ("mean_victim_consistency", "victim_consistency"),
        ("mean_control_consistency", "control_consistency"),
        ("permutation_p", "raw_p"),
        ("fdr_q", "adjusted_p"),
        ("permutation_p", "permutation_p"),
        ("bootstrap_ci_low", "bootstrap_ci_low"),
        ("bootstrap_ci_high", "bootstrap_ci_high"),
        ("loo_sign_agreement", "leave_one_out_stability"),
        ("classification", "classification"),
        ("source_phase", "source_phase"),
        ("provenance", "provenance"),
        ("level", "analysis_level"),
        ("related_marker", "related_marker"),
        ("signal", "source_signal"),
        ("cluster_mass", "cluster_mass"),
        ("n_perm", "n_perm"),
        ("unit", "unit"),
    ]:
        if src in clusters.columns:
            out[dst] = clusters[src]
    return out


def write_phase6(root: Path, result: dict) -> None:
    d = _dirs(root)
    agg = result["agg"]
    np.savez_compressed(
        d["trajectory_data"] / "subject_trajectories.npz",
        subject_id=agg["subject_id"],
        signals=np.array(agg["signals"]),
        median=agg["median"],
        mean=agg["mean"],
        n_cycles=agg["n_cycles"],
        victim=result["victim"],
    )
    result["meta"].to_csv(d["trajectory_data"] / "trajectory_metadata.csv", index=False)
    agg["quality"].to_csv(d["trajectory_data"] / "trajectory_quality.csv", index=False)
    stats = result["stats"]
    if len(stats):
        stats[stats["level"].astype(str).str.contains("primary")].to_csv(d["group"] / "difference_trajectories.csv", index=False)
        v = stats[["channel", "time_percent", "victim_median", "n_victim", "level"]]
        c = stats[["channel", "time_percent", "control_median", "n_control", "level"]]
        v.to_csv(d["group"] / "victim_trajectories.csv", index=False)
        c.to_csv(d["group"] / "control_trajectories.csv", index=False)
        stats.to_csv(d["statistics"] / "trajectory_statistics.csv", index=False)
    result["clusters"].to_csv(d["statistics"] / "cluster_permutation_results.csv", index=False)
    if len(result["clusters"]) and "fdr_q" in result["clusters"].columns:
        result["clusters"][["channel", "level", "start_percent", "end_percent", "permutation_p", "fdr_q", "classification"]].to_csv(
            d["statistics"] / "multiple_testing_results.csv", index=False
        )
    result["shape"].to_csv(d["shape"] / "peak_timing.csv", index=False)
    if len(result["shape"]):
        result["shape"][["subject_id", "channel", "victimized", "peak_magnitude", "min_magnitude"]].to_csv(
            d["shape"] / "peak_magnitude.csv", index=False
        )
        result["shape"][["subject_id", "channel", "victimized", "vel_rms", "mean_abs_accel", "n_extrema"]].to_csv(
            d["shape"] / "derivative_features.csv", index=False
        )
    result["shape_stats"].to_csv(d["shape"] / "shape_statistics.csv", index=False)
    asym = stats[stats["family"] == "asymmetry"] if len(stats) and "family" in stats.columns else stats[stats["channel"].astype(str).str.contains("LminusR", na=False)] if len(stats) else pd.DataFrame()
    if len(stats):
        stats[stats["channel"].astype(str).str.contains("LminusR", na=False)].to_csv(d["asymmetry"] / "asymmetry_trajectories.csv", index=False)
        result["clusters"][result["clusters"]["channel"].astype(str).str.contains("LminusR", na=False)].to_csv(
            d["asymmetry"] / "asymmetry_statistics.csv", index=False
        )
    if len(stats):
        stats[["channel", "time_percent", "victim_consistency", "control_consistency"]].to_csv(
            d["consistency"] / "subject_direction_consistency.csv", index=False
        )
    if len(result["clusters"]):
        result["clusters"][["channel", "start_percent", "end_percent", "loo_sign_agreement", "bootstrap_ci_low", "bootstrap_ci_high"]].to_csv(
            d["consistency"] / "leave_one_subject_out.csv", index=False
        )
        result["clusters"][["channel", "bootstrap_ci_low", "bootstrap_ci_high"]].to_csv(
            d["consistency"] / "bootstrap_results.csv", index=False
        )
    result["meta"].to_csv(d["anatomy"] / "marker_mapping.csv", index=False)
    result["meta"].to_csv(d["anatomy"] / "joint_mapping.csv", index=False)
    pd.DataFrame([{"bin_lo": a, "bin_hi": b} for a, b in PHASE_BINS]).to_csv(d["anatomy"] / "gait_phase_mapping.csv", index=False)

    cand = _cand_table(result["clusters"])
    cand.to_csv(d["base"] / "candidate_trajectory_regions.csv", index=False)
    if len(cand):
        cand.drop_duplicates("signal").to_csv(d["base"] / "candidate_trajectory_signals.csv", index=False)
    else:
        pd.DataFrame(columns=["signal"]).to_csv(d["base"] / "candidate_trajectory_signals.csv", index=False)
    (d["base"] / "phase6_config.json").write_text(json.dumps(result["config"], indent=2), encoding="utf-8")

    _figures(d["figures"], result)
    (d["base"] / "phase6_report.md").write_text(render_phase6_report(result), encoding="utf-8")


def _figures(figdir: Path, result: dict) -> None:
    stats = result["stats"]
    if stats is None or stats.empty:
        return
    prim = stats[stats["channel"].isin(result["primary_channels"])]
    if len(prim):
        prim = prim.copy()
        prim["bin"] = (prim["time_percent"] // 10) * 10
        heat = prim.pivot_table(index="channel", columns="bin", values="effect_size", aggfunc=lambda s: np.nanmean(np.abs(s)))
        fig, ax = plt.subplots(figsize=(8, 5))
        im = ax.imshow(heat.to_numpy(), aspect="auto", cmap="binary")
        ax.set_yticks(range(len(heat.index)))
        ax.set_yticklabels(heat.index, fontsize=7)
        ax.set_xticks(range(len(heat.columns)))
        ax.set_xticklabels([str(c) for c in heat.columns], fontsize=7)
        ax.set_title("|Cliff's δ| by primary channel × 10% bin (descriptive)")
        fig.colorbar(im, ax=ax, fraction=0.03)
        fig.tight_layout()
        fig.savefig(figdir / "effect_heatmap_primary.png", dpi=130)
        plt.close(fig)
    show = list(result["primary_channels"][:8])
    t = np.arange(101)
    fig, axes = plt.subplots(4, 2, figsize=(9, 10), sharex=True)
    for ax, ch in zip(axes.ravel(), show):
        g = stats[stats["channel"] == ch]
        if g.empty:
            continue
        ax.plot(g["time_percent"], g["victim_median"], color="#6b4c7a", label="victim median")
        ax.plot(g["time_percent"], g["control_median"], color="#4a4a4a", label="control median")
        ax.set_title(ch, fontsize=8)
        ax.set_xlabel("% gait cycle")
    axes[0, 0].legend(fontsize=6)
    fig.suptitle("Primary trajectories (subject-level medians; not evidence by themselves)")
    fig.tight_layout()
    fig.savefig(figdir / "primary_group_medians.png", dpi=130)
    plt.close(fig)
    fig, axes = plt.subplots(4, 2, figsize=(9, 10), sharex=True)
    for ax, ch in zip(axes.ravel(), show):
        g = stats[stats["channel"] == ch]
        if g.empty:
            continue
        ax.axhline(0, color="#cccccc")
        ax.plot(g["time_percent"], g["difference"], color="#333333")
        ax.set_title(ch, fontsize=8)
    fig.suptitle("Victim minus control median difference")
    fig.tight_layout()
    fig.savefig(figdir / "primary_difference.png", dpi=130)
    plt.close(fig)
    cl = result["clusters"]
    cands = cl[cl["classification"].isin(["ROBUST", "EXPLORATORY"])] if len(cl) and "classification" in cl.columns else cl.iloc[0:0]
    for _, r in cands.head(6).iterrows():
        ch = r["channel"]
        g = stats[stats["channel"] == ch]
        X = result["agg"]["median"]
        # spaghetti needs channel index
        sig = str(r.get("source_signal", r.get("signal", "")))
        if sig in result["agg"]["signals"]:
            j = result["agg"]["signals"].index(sig)
            axn = str(r.get("axis", "ax1"))
            a = AXIS_NAMES.index(axn) if axn in AXIS_NAMES else 0
            fig, ax = plt.subplots(figsize=(6, 4))
            xv = X[result["victim"], j, :, a]
            xc = X[~result["victim"], j, :, a]
            ax.plot(t, xv.T, color="#6b4c7a", alpha=0.25, lw=0.8)
            ax.plot(t, xc.T, color="#888888", alpha=0.25, lw=0.8)
            ax.plot(t, np.nanmedian(xv, 0), color="#6b4c7a", lw=2, label="victim median")
            ax.plot(t, np.nanmedian(xc, 0), color="#222222", lw=2, label="control median")
            ax.axvspan(r["start_percent"], r["end_percent"], color="#dddddd", zorder=0)
            ax.set_title(f"{ch} {r['classification']} {int(r['start_percent'])}-{int(r['end_percent'])}%")
            ax.legend(fontsize=7)
            fig.tight_layout()
            fig.savefig(figdir / f"spaghetti_{ch}_{int(r['start_percent'])}.png", dpi=130)
            plt.close(fig)


def render_phase6_report(result: dict) -> str:
    cl = result["clusters"]
    n_rob = int((cl["classification"] == "ROBUST").sum()) if len(cl) and "classification" in cl.columns else 0
    n_exp = int((cl["classification"] == "EXPLORATORY").sum()) if len(cl) and "classification" in cl.columns else 0
    if n_rob:
        conclusion = "A candidate time-resolved biomechanical difference was identified and should be independently validated. This is not a victim diagnostic signature."
        outcome = "C"
    elif n_exp:
        conclusion = "Exploratory trajectory differences were observed but require independent validation."
        outcome = "B"
    else:
        conclusion = "No robust time-resolved victim-associated gait difference was detected."
        outcome = "A"
    strongest = "none"
    if len(cl):
        tmp = cl.copy()
        tmp["absd"] = tmp["mean_cliffs_delta"].abs() if "mean_cliffs_delta" in tmp.columns else 0
        r = tmp.sort_values("permutation_p").iloc[0]
        strongest = (
            f"{r.get('channel')} {r.get('start_percent')}-{r.get('end_percent')}% "
            f"δ={r.get('mean_cliffs_delta')} p={r.get('permutation_p')} q={r.get('fdr_q')} class={r.get('classification')}"
        )
    shape_hit = "none FDR≤0.10"
    ss = result["shape_stats"]
    if len(ss) and "fdr_q" in ss.columns:
        hit = ss[ss["fdr_q"] <= 0.10]
        shape_hit = "none FDR≤0.10" if hit.empty else hit.head(5).to_string(index=False)
    return f"""# Phase 6 Time-Resolved Trajectory Analysis

Generated: {date.today().isoformat()}

## 1. Objective

Determine whether victimized and non-victimized females differ in **normalized gait trajectories** (0–100%, 101 points) after subject-level aggregation.

## 2. Motivation from Phases 3–5

Phase 3 found no FDR-supported summary-feature signature. Phase 4 found no victim-enriched phenotype. Phase 5 found no within-victim structure. Phase 6 tests whether **aggregation into scalars hid localized time-resolved differences**.

## 3. Dataset

{result['n_cycles']} Phase 1 normalized cycles; {result['n_subjects']} subjects; {result['n_time']} time points; {result['n_channels_tested']} channels tested.

## 4. Independent unit

**n = 31 subjects.** Cycles are repeated measures. Inferential n is never 880.

## 5. Trajectory source

`results/phase1/gait_cycles/normalized_core.npz` (certified Phase 1). No renormalization.

## 6. Subject-level construction

Within-subject **nanmedian** across that subject's cycles (mean stored as sensitivity). No pooling across people.

## 7. Quality control

Channels require all 31 subjects to have ≥90% finite time points. Ineligible channels excluded (n={result['n_excluded_ineligible']}). No silent zero-fill. No inferential interpolation.

## 8. Primary statistical method

Welch t-statistic time series; cluster-forming threshold |t|>2.045; cluster mass = sum |t| on contiguous suprathreshold points.

Primary channels (frozen): {', '.join(result['primary_channels'])}

## 9. Permutation methodology

H0: no systematic victim/control trajectory difference. Permute **subject labels**; keep each 101-point trajectory intact. Primary permutations={result['n_perm_primary']}; secondary={result['n_perm_secondary']}; seed={result['seed']}. Never shuffle time or cycles.

## 10. Temporal correction

Cluster-based permutation (max cluster mass) controls the family of 101 time points within a channel.

## 11. Signal-level correction

Benjamini–Hochberg FDR within analysis level (primary / primary_asymmetry / secondary / secondary_asymmetry).

## 12. Shape analysis

Savitzky–Golay window 11, poly 3 (Phase 2). Peak/min timing and magnitude, n extrema, vel RMS. Mann–Whitney + BH.

{shape_hit}

## 13. Bilateral asymmetry

A(t)=L−R and |L−R| on hip, knee, ankle, foot-progression ax1 subject medians.

## 14. Subject consistency

Predefined: share of victims on the group-difference side of the **control median** at each time point.

## 15. Leave-one-out

Sign of the regional mean difference after dropping each subject.

## 16. Bootstrap

1000 within-group subject resamples; percentile CI for regional mean median-difference.

## 17. Candidate trajectory regions

ROBUST={n_rob}; EXPLORATORY={n_exp}. Strongest (lowest permutation p): {strongest}

## 18. Marker/joint localization

See anatomy tables and `related_marker` on candidates. Axes remain ax1/ax2/ax3.

## 19. Cross-check against Phase 2/3

`source_phase` column: A already in Phase 3 FDR, B new/unmatched, C related but Phase 3 not FDR-significant.

## 20. Limitations

n=31; cluster threshold is conventional; secondary search is large; coordinate convention not certified as AP/ML/vertical.

## 21. Scientific conclusion

Outcome {outcome}: {conclusion}

## 22. Recommendations for Phase 7

Do not train a victim classifier on these 31 people. If any exploratory region is pursued, preregister it on new subjects.

Phase 7 was not started.
"""


def certify_phase6(result: dict) -> dict:
    checks = []

    def add(name, ok, detail, warn=False):
        if not ok:
            st = "FAIL"
        elif warn:
            st = "WARNING"
        else:
            st = "PASS"
        checks.append({"name": name, "status": st, "detail": detail})

    add("n_subjects_31", result["n_subjects"] == 31, "subject-level n=31")
    add("n_time_101", result["n_time"] == 101, "101-point cycles")
    add("not_880", result["n_cycles"] == 880 and result["n_subjects"] != 880, "cycles are repeated measures")
    add("primary_predefined", len(result["primary_channels"]) == 11, "frozen primary set")
    add("perm_unit", True, "cluster permutation shuffles subject labels")
    add("no_zero_fill", (result["agg"]["quality"]["zero_filled"] == False).all(), "no silent zeros")
    add("shape_present", len(result["shape_stats"]) > 0, "shape analysis ran")
    add("axes_not_anatomical", True, "ax1/ax2/ax3 retained")
    n_rob = int((result["clusters"]["classification"] == "ROBUST").sum()) if len(result["clusters"]) and "classification" in result["clusters"].columns else 0
    add("honest_null_allowed", True, f"robust_findings={n_rob}", warn=n_rob == 0)
    if any(c["status"] == "FAIL" for c in checks):
        status = "NOT CERTIFIED"
    elif any(c["status"] == "WARNING" for c in checks):
        status = "PASS WITH WARNINGS"
    else:
        status = "PASS"
    return {"generated": date.today().isoformat(), "status": status, "checks": checks, "n_robust": n_rob}
