"""Phase 6 orchestration. Preprocessing frozen before group tests. No predictive ML."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..features.anatomy import SIGNAL_ANATOMY
from ..features.base import AXIS_NAMES, PHASE_BINS
from ..labels import load_female_labels
from ..statistics.multiple_testing import benjamini_hochberg
from .aggregate import subject_median_trajectories
from .asymmetry import asymmetry_channels
from .cluster_perm import cluster_permutation, permute_labels
from .load import load_normalized_cube, signal_family
from .robustness import bootstrap_region_ci, region_loo
from .shape import compare_shape, shape_table

SEED = 20260813
N_PERM_PRIMARY = 9999
N_PERM_SECONDARY = 1999
N_BOOT = 1000

# Frozen before any victim/control inspection of trajectories.
PRIMARY_CHANNELS = (
    "LHipAngles_ax1",
    "RHipAngles_ax1",
    "LKneeAngles_ax1",
    "RKneeAngles_ax1",
    "LAnkleAngles_ax1",
    "RAnkleAngles_ax1",
    "LFootProgressAngles_ax1",
    "RFootProgressAngles_ax1",
    "CentreOfMass_ax1",
    "CentreOfMass_ax2",
    "CentreOfMass_ax3",
)
PRIMARY_ASYM = (
    "HipAngles_ax1_LminusR",
    "HipAngles_ax1_absLminusR",
    "KneeAngles_ax1_LminusR",
    "KneeAngles_ax1_absLminusR",
    "AnkleAngles_ax1_LminusR",
    "AnkleAngles_ax1_absLminusR",
)


def _labels(root: Path, subject_id: np.ndarray) -> np.ndarray:
    lab = load_female_labels(root / "data" / "raw" / "Victimization surveys.xlsx")
    m = dict(zip(lab["subject_id"], lab["victimized"]))
    y = np.array([m.get(s) for s in subject_id])
    if (y == "Y").sum() != 17 or (y == "N").sum() != 14:
        raise RuntimeError("expected 17/14 labels aligned to subject trajectories")
    return y == "Y"


def _phase3_lookup(root: Path) -> pd.DataFrame | None:
    p = root / "results" / "phase3" / "statistics" / "group_comparisons.csv"
    if not p.is_file():
        return None
    return pd.read_csv(p)


def _crosscheck(channel: str, p3: pd.DataFrame | None) -> str:
    if p3 is None or "feature" not in p3.columns:
        return "phase3_table_missing"
    stem = channel.replace("_LminusR", "").replace("_absLminusR", "")
    hits = p3[p3["feature"].astype(str).str.contains(stem.split("_ax")[0] if "_ax" in stem else stem, regex=False)]
    if hits.empty:
        return "B_new_or_unmatched"
    q = pd.to_numeric(hits.get("fdr_q", hits.get("raw_p")), errors="coerce")
    if q.notna().any() and float(q.min()) <= 0.10:
        return "A_already_captured_by_phase3"
    return "C_related_but_phase3_not_fdr_significant"


def classify(row: pd.Series) -> str:
    n_pts = int(row["end_idx"] - row["start_idx"] + 1)
    ci_excl = (
        np.isfinite(row.get("bootstrap_ci_low", np.nan))
        and np.isfinite(row.get("bootstrap_ci_high", np.nan))
        and (row["bootstrap_ci_low"] * row["bootstrap_ci_high"] > 0)
    )
    robustish = (
        float(row.get("fdr_q", 1)) <= 0.10
        and abs(float(row.get("mean_cliffs_delta", 0))) >= 0.33
        and float(row.get("mean_victim_consistency", 0)) >= 0.60
        and float(row.get("loo_sign_agreement", 0)) >= 0.80
        and ci_excl
        and n_pts >= 3
    )
    if row.get("level") == "primary" and robustish:
        return "ROBUST"
    if float(row.get("permutation_p", 1)) < 0.05:
        return "EXPLORATORY"
    if robustish:
        return "EXPLORATORY"
    return "UNSUPPORTED"


def run_phase6(
    project_root: Path,
    *,
    n_perm_primary: int = N_PERM_PRIMARY,
    n_perm_secondary: int = N_PERM_SECONDARY,
    n_boot: int = N_BOOT,
) -> dict:
    loaded = load_normalized_cube(project_root)
    agg = subject_median_trajectories(loaded["cube"], loaded["inventory"], loaded["signals"])
    if agg["n_subjects"] != 31:
        raise RuntimeError(f"expected 31 subjects, got {agg['n_subjects']}")
    # Live confirmatory analysis requires full cohort coverage.
    agg["quality"]["eligible"] = (agg["quality"]["n_subjects_ok"] == 31) & (agg["quality"]["n_subjects"] == 31)
    victim = _labels(project_root, agg["subject_id"])
    p3 = _phase3_lookup(project_root)
    qmap = {(r.signal, r.axis): r.eligible for r in agg["quality"].itertuples()}

    perm_pri = permute_labels(victim, n_perm_primary, SEED)
    perm_sec = permute_labels(victim, n_perm_secondary, SEED + 1)

    channels: list[tuple[str, np.ndarray, str, dict]] = []
    meta_rows = []
    for j, sig in enumerate(agg["signals"]):
        ana = SIGNAL_ANATOMY.get(sig, {})
        for ax, axn in enumerate(AXIS_NAMES):
            key = f"{sig}_{axn}"
            eligible = bool(qmap.get((sig, axn), False))
            level = "primary" if key in PRIMARY_CHANNELS else "secondary"
            fam = signal_family(sig)
            meta_rows.append(
                {
                    "channel": key,
                    "signal": sig,
                    "axis": axn,
                    "family": fam,
                    "level": level,
                    "anatomical_region": ana.get("region", "unknown"),
                    "side": ana.get("side", "unknown"),
                    "related_marker": ana.get("related", sig),
                    "eligible": eligible,
                }
            )
            if not eligible:
                continue
            X = agg["median"][:, j, :, ax]
            channels.append((key, X, level, {"signal": sig, "axis": axn, "family": fam, "anatomy": ana}))

    for name, X in asymmetry_channels(agg["median"], agg["signals"], axis=0).items():
        level = "primary_asymmetry" if name in PRIMARY_ASYM else "secondary_asymmetry"
        channels.append(
            (
                name,
                X,
                level,
                {
                    "signal": name,
                    "axis": "ax1",
                    "family": "asymmetry",
                    "anatomy": {"region": "bilateral", "side": "bilateral", "related": name},
                },
            )
        )
        meta_rows.append(
            {
                "channel": name,
                "signal": name,
                "axis": "ax1",
                "family": "asymmetry",
                "level": level,
                "anatomical_region": "bilateral",
                "side": "bilateral",
                "related_marker": name,
                "eligible": True,
            }
        )

    cluster_rows = []
    stat_rows = []
    curves = {}
    for key, X, level, info in channels:
        n_perm = n_perm_primary if level.startswith("primary") else n_perm_secondary
        plab = perm_pri if level.startswith("primary") else perm_sec
        if plab.shape[0] != n_perm:
            plab = plab[:n_perm]
        cp = cluster_permutation(X, victim, n_perm=n_perm, seed=SEED, perm_labels=plab)
        curves[key] = cp
        t = np.arange(X.shape[1])
        for tt in t:
            stat_rows.append(
                {
                    "channel": key,
                    "time_percent": int(tt),
                    "victim_median": cp["victim_median"][tt],
                    "control_median": cp["control_median"][tt],
                    "difference": cp["difference"][tt],
                    "effect_size": cp["delta"][tt],
                    "t_stat": cp["t_obs"][tt],
                    "victim_consistency": cp["victim_consistency"][tt],
                    "control_consistency": cp["control_consistency"][tt],
                    "n_victim": 17,
                    "n_control": 14,
                    "level": level,
                }
            )
        ana = info["anatomy"]
        for cl in cp["clusters"]:
            cluster_rows.append(
                {
                    "channel": key,
                    "level": level,
                    "signal": info["signal"],
                    "axis": info["axis"],
                    "family": info["family"],
                    "anatomical_region": ana.get("region", "unknown"),
                    "side": ana.get("side", "unknown"),
                    "related_marker": ana.get("related", info["signal"]),
                    **cl,
                    "n_perm": cp["n_perm"],
                    "unit": "subject",
                }
            )

    clusters = pd.DataFrame(cluster_rows)
    stats = pd.DataFrame(stat_rows)
    meta = pd.DataFrame(meta_rows)

    if len(clusters):
        clusters["fdr_q"] = np.nan
        for level, idx in clusters.groupby("level").groups.items():
            clusters.loc[idx, "fdr_q"] = benjamini_hochberg(clusters.loc[idx, "permutation_p"].to_numpy())
        xmap = {k: x for k, x, _, _ in channels}
        loo_a, blo, bhi = [], [], []
        for r in clusters.itertuples():
            X = xmap[r.channel]
            lo = region_loo(X, victim, int(r.start_idx), int(r.end_idx))
            ci_lo, ci_hi, _, _ = bootstrap_region_ci(X, victim, int(r.start_idx), int(r.end_idx), n_boot=n_boot, seed=SEED)
            loo_a.append(lo["loo_sign_agreement"])
            blo.append(ci_lo)
            bhi.append(ci_hi)
        clusters["loo_sign_agreement"] = loo_a
        clusters["bootstrap_ci_low"] = blo
        clusters["bootstrap_ci_high"] = bhi
        clusters["classification"] = clusters.apply(classify, axis=1)
        clusters["source_phase"] = clusters["channel"].map(lambda c: _crosscheck(c, p3))
        clusters["provenance"] = "phase1_normalized_core.npz|subject_nanmedian|cluster_perm_subject_labels"
    else:
        clusters = pd.DataFrame(
            columns=[
                "channel",
                "level",
                "start_percent",
                "end_percent",
                "permutation_p",
                "fdr_q",
                "classification",
            ]
        )

    # shape on primary angle/COM channels
    shape_parts = []
    for key, X, level, info in channels:
        if level != "primary":
            continue
        shape_parts.append(shape_table(X, agg["subject_id"], victim, key))
    shape_df = pd.concat(shape_parts, ignore_index=True) if shape_parts else pd.DataFrame()
    shape_stats = (
        compare_shape(
            shape_df,
            ("peak_timing_pct", "min_timing_pct", "peak_magnitude", "min_magnitude", "vel_rms", "n_extrema"),
        )
        if len(shape_df)
        else pd.DataFrame()
    )

    # phase-bin secondary summaries for primary channels
    bin_rows = []
    for key, X, level, info in channels:
        if level != "primary":
            continue
        for lo, hi in PHASE_BINS:
            sl = slice(lo, hi if hi < 100 else 101)
            for i, sid in enumerate(agg["subject_id"]):
                seg = X[i, sl]
                bin_rows.append(
                    {
                        "subject_id": sid,
                        "channel": key,
                        "phase_lo": lo,
                        "phase_hi": hi,
                        "bin_median": float(np.nanmedian(seg)),
                        "bin_mean": float(np.nanmean(seg)),
                        "bin_std": float(np.nanstd(seg)),
                        "victimized": "Y" if victim[i] else "N",
                    }
                )
    bins = pd.DataFrame(bin_rows)

    n_excl = int((~meta["eligible"]).sum()) if "eligible" in meta.columns else 0
    return {
        "loaded": loaded,
        "agg": agg,
        "victim": victim,
        "meta": meta,
        "stats": stats,
        "clusters": clusters,
        "curves": curves,
        "shape": shape_df,
        "shape_stats": shape_stats,
        "phase_bins": bins,
        "n_subjects": 31,
        "n_cycles": int(loaded["cube"].shape[0]),
        "n_time": 101,
        "n_perm_primary": n_perm_primary,
        "n_perm_secondary": n_perm_secondary,
        "n_boot": n_boot,
        "seed": SEED,
        "n_channels_tested": len(channels),
        "n_excluded_ineligible": n_excl,
        "primary_channels": PRIMARY_CHANNELS,
        "config": {
            "aggregation": "subject_nanmedian",
            "cluster_threshold_|t|": 2.045,
            "n_perm_primary": n_perm_primary,
            "n_perm_secondary": n_perm_secondary,
            "seed": SEED,
            "axes": "ax1/ax2/ax3_not_AP_ML_vertical",
            "interpolation": "none_on_inferential_trajectories",
        },
    }
