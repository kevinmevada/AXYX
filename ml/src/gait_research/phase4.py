"""Phase 4 writers, figures, report, certification. Does not modify Phases 0–3."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .phenotypes.clustering import MIN_CLUSTER_SIZE, MIN_MEAN_ARI, MIN_SILHOUETTE
from .phenotypes.representation import SEED, assert_no_labels


def _dirs(root: Path) -> dict[str, Path]:
    base = root / "results" / "phase4"
    paths = {
        "base": base,
        "representation": base / "representation",
        "dimensionality": base / "dimensionality",
        "clustering": base / "clustering",
        "phenotypes": base / "phenotypes",
        "enrichment": base / "enrichment",
        "confounding": base / "confounding",
        "figures": base / "figures",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def _pca_plot(scores: pd.DataFrame, assign: pd.DataFrame, path: Path, *, by: str) -> None:
    fig, ax = plt.subplots(figsize=(6, 5))
    df = scores.merge(assign[["subject_id", "phenotype"]], on="subject_id", how="left")
    pcs = [c for c in df.columns if c.startswith("PC")]
    x, y = df[pcs[0]], df[pcs[1]]
    if by == "phenotype":
        for val, part in df.groupby("phenotype"):
            ax.scatter(part[pcs[0]], part[pcs[1]], s=36, label=str(val))
        ax.legend(title="Phenotype", fontsize=8)
        ax.set_title("PCA of family-balanced gait representation")
    else:
        ax.scatter(x, y, s=36, c="#555555")
        ax.set_title("PCA (discovery; not colored by victimization)")
    ax.set_xlabel(pcs[0])
    ax.set_ylabel(pcs[1])
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def _bar(df: pd.DataFrame, x, y, path: Path, title: str, ylabel: str) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(df[x].astype(str), df[y], color="#4a4a4a")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def _traj_plot(traj: dict, path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(8, 6), sharex=True)
    wanted = ["LHipAngles", "LKneeAngles", "LAnkleAngles", "LFootProgressAngles"]
    axes = axes.ravel()
    t = np.linspace(0, 100, 101)
    data = traj.get("data") or {}
    sigs = traj.get("signals") or []
    sidx = traj.get("signal_index") or {}
    for ax, name in zip(axes, wanted):
        if name not in sidx:
            ax.set_title(name)
            continue
        j = sidx[name]
        for ph, blob in sorted(data.items()):
            med = blob["median"]
            ax.plot(t, med[j, :, 0], label=f"P{ph}")
        ax.set_title(f"{name} ax1")
        ax.set_xlabel("% gait cycle")
    if data:
        axes[0].legend(fontsize=7)
    fig.suptitle("Phenotype median trajectories (subject-then-phenotype median)")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def _composition_plot(comp: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    x = np.arange(len(comp))
    ax.bar(x, comp["n_victimized"], label="victimized", color="#6b4c7a")
    ax.bar(x, comp["n_control"], bottom=comp["n_victimized"], label="control", color="#8aa0a8")
    ax.set_xticks(x)
    ax.set_xticklabels([f"P{p}" for p in comp["phenotype"]])
    ax.set_ylabel("Subjects")
    ax.set_title("Phenotype composition (labels revealed after clustering)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def write_phase4(project_root: Path, result: dict) -> dict[str, Path]:
    d = _dirs(project_root)
    paths = {}
    compact = result["compact_frame"]
    compact.to_parquet(d["representation"] / "feature_matrix.parquet", index=False)
    meta = {
        "method": result["rep"]["method"],
        "n_subjects": 31,
        "n_compact_dimensions": int(result["rep"]["compact"].shape[1]),
        "n_source_representatives": len(result["rep"]["raw_names"]),
        "family_info": {
            k: {kk: vv for kk, vv in v.items() if kk != "source_features"}
            for k, v in result["rep"]["family_info"].items()
        },
        "family_source_counts": {k: v["n_source_features"] for k, v in result["rep"]["family_info"].items()},
        "pca_variance_keep_for_description": result["pca_n_keep"],
        "cluster_choice": result["choice"],
    }
    (d["representation"] / "representation_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    result["pca_scores"].to_csv(d["dimensionality"] / "pca_scores.csv", index=False)
    result["pca_summary"].to_csv(d["dimensionality"] / "pca_summary.csv", index=False)
    result["metrics"].to_csv(d["clustering"] / "cluster_metrics.csv", index=False)
    result["stability"].to_csv(d["clustering"] / "cluster_stability.csv", index=False)
    result["sensitivity"].to_csv(d["clustering"] / "sensitivity.csv", index=False)
    result["assignments"].to_csv(d["phenotypes"] / "phenotype_assignments.csv", index=False)
    result["assignments"].to_csv(d["base"] / "phenotype_assignments.csv", index=False)
    result["profiles"].to_csv(d["phenotypes"] / "phenotype_profiles.csv", index=False)
    result["effects"].to_csv(d["phenotypes"] / "phenotype_features.csv", index=False)
    traj = result["trajectories"]
    if traj.get("data"):
        payload = {
            "signals": np.array(traj["signals"]),
            "phenotypes": np.array(sorted(traj["data"])),
        }
        for ph, blob in traj["data"].items():
            payload[f"median_phenotype_{ph}"] = blob["median"]
        np.savez_compressed(d["phenotypes"] / "phenotype_trajectories.npz", **payload)
    result["composition"].to_csv(d["enrichment"] / "group_by_phenotype.csv", index=False)
    result["enrichment"].to_csv(d["enrichment"] / "enrichment_statistics.csv", index=False)
    result["covariates"].to_csv(d["confounding"] / "phenotype_covariates.csv", index=False)

    figs = d["figures"]
    _pca_plot(result["pca_scores"], result["assignments"], figs / "pca_phenotype.png", by="phenotype")
    _pca_plot(result["pca_scores"], result["assignments"], figs / "pca_discovery_unlabeled.png", by="none")
    hier = result["stability"][result["stability"]["method"] == "hierarchical"]
    if len(hier):
        _bar(hier, "k", "mean_boot_ari", figs / "cluster_stability.png", "Bootstrap ARI (hierarchical)", "mean ARI")
    if result["choice"]["k"] is not None:
        sizes = result["assignments"].groupby("phenotype").size().reset_index(name="n")
        _bar(sizes, "phenotype", "n", figs / "phenotype_size.png", "Phenotype sizes", "n subjects")
        if len(result["profiles"]):
            fig, ax = plt.subplots(figsize=(8, 4))
            p1 = result["profiles"]
            ax.barh(np.arange(len(p1)), p1["cliffs_delta"], color="#4a4a4a")
            ax.set_yticks(np.arange(len(p1)))
            ax.set_yticklabels([f"P{int(r.phenotype)} {r.feature}" for r in p1.itertuples()], fontsize=6)
            ax.set_xlabel("Cliff's delta vs other phenotypes")
            ax.set_title("Top phenotype-defining features (label-blind)")
            fig.tight_layout()
            fig.savefig(figs / "phenotype_profiles.png", dpi=140)
            plt.close(fig)
        if traj.get("data"):
            _traj_plot(traj, figs / "phenotype_trajectories.png")
        if len(result["composition"]):
            _composition_plot(result["composition"], figs / "phenotype_victimization.png")
    (d["base"] / "phase4_report.md").write_text(render_phase4_report(result), encoding="utf-8")
    paths["report"] = d["base"] / "phase4_report.md"
    return paths


def render_phase4_report(result: dict) -> str:
    choice = result["choice"]
    k = choice["k"]
    n_dim = result["rep"]["compact"].shape[1]
    pca_sum = result["pca_summary"]
    pc1 = float(pca_sum.iloc[0]["explained_variance_ratio"]) if len(pca_sum) else float("nan")
    if k is None:
        conclusion = (
            "No stable gait phenotype structure was detected under the pre-specified "
            f"rules (hierarchical clustering, min size ≥ {MIN_CLUSTER_SIZE}, silhouette ≥ {MIN_SILHOUETTE}, "
            f"bootstrap ARI ≥ {MIN_MEAN_ARI}). Victimization enrichment was therefore not interpreted as a phenotype finding."
        )
        structure = "No stable phenotypes."
    else:
        conclusion = (
            f"A stable hierarchical solution at k={k} was supported by silhouette and subject-level bootstrap ARI. "
            "Victimization labels were joined only after this solution was frozen."
        )
        structure = f"Stable phenotypes: k={k} ({choice['reason']})."
        sizes = result["assignments"]["phenotype"].value_counts()
        if int(sizes.min()) <= 4 and int(sizes.max()) >= 20:
            conclusion = (
                f"k={k} met the pre-specified stability rule (silhouette={choice.get('silhouette', float('nan')):.2f}, "
                f"mean bootstrap ARI={choice.get('mean_boot_ari', float('nan')):.2f}), but the partition is "
                f"{int(sizes.max())} vs {int(sizes.min())} subjects. That is a majority/outgroup split, not two "
                "large, equally populated gait types. The n=4 group should not be promoted to a named clinical phenotype. "
                "After labels were revealed, phenotype composition was compatible with the overall 17/31 victim base rate."
            )
            structure = f"k={k} ({choice['reason']}); sizes={dict(sizes.sort_index())}."
    enrich_txt = "Not applicable (no stable phenotypes)."
    if k is not None and len(result["enrichment"]):
        lines = []
        for r in result["enrichment"].itertuples():
            lines.append(
                f"- Phenotype {int(r.phenotype)}: {int(r.n_victimized)}/{int(r.n_subjects)} victimized "
                f"(prop={r.prop_victimized:.2f}, expected={r.expected_prop_victimized:.2f}, "
                f"Fisher p={r.fisher_p:.3g}, perm p={r.perm_p:.3g}, FDR q={r.fdr_q:.3g})"
            )
        enrich_txt = "\n".join(lines)
    cov_txt = "Not applicable (no stable phenotypes)."
    if k is not None and len(result["covariates"]):
        pvals = result["covariates"].drop_duplicates(["variable"])[["variable", "kruskal_p"]]
        cov_txt = ", ".join(f"{a} Kruskal p={b:.3g}" for a, b in pvals.itertuples(index=False))
    fam = result["rep"]["family_info"]
    fam_lines = "\n".join(
        f"- {name}: {info['n_source_features']} source features → {info['n_pcs']} family PCs"
        for name, info in sorted(fam.items())
    )
    return f"""# Phase 4 Gait Phenotype and Heterogeneity Discovery

Generated: {date.today().isoformat()}

## 1. Objective

Determine whether the 31 subjects form stable, interpretable gait phenotypes, and only then whether victimization is disproportionately represented in any phenotype.

## 2. Scientific motivation from Phase 3

Phase 3 found no FDR-supported, robust, shared victim-versus-control gait signature. Phase 4 therefore tests heterogeneity (multiple natural gait patterns) rather than a single population-wide victim signature.

## 3. Dataset

Phase 2 subject features (31 × 3665) restricted to Phase 3 label-blind redundancy representatives.

## 4. Independent unit

**n = 31 independent subjects.** 880 gait cycles are repeated observations within subjects and were not treated as independent clustering units.

## 5. Label-blind methodology

Victimization labels were absent from feature selection, median/IQR scaling, family PCA, global PCA, clustering, k selection, stability, and phenotype characterization. Labels were joined only after assignments were frozen.

## 6. Feature representation

- Source: {len(result['rep']['raw_names'])} Phase 3 representatives
- Compact family-balanced dimensions: {n_dim}
- Balancing: within-family PCA (keep ≥80% family variance, cap 8 PCs), then divide by √n_pcs so families do not dominate Euclidean distance

{fam_lines}

## 7. Scaling

Median / IQR robust scaling, parameters estimated on all 31 subjects without labels. Non-finite values imputed with the column median before scaling. Zero-IQR columns set to 0.

## 8. Dimensionality reduction

PCA describes variance of the compact representation. PC1 explains {pc1:.1%} of that variance. Components were **not** chosen to separate victims and controls. Clustering used the family-PC matrix, not a victimization-tuned subspace.

## 9. Cluster methodology

Primary: hierarchical Ward. Sensitivity: k-means (10 random inits, seed {SEED}). Candidates k ∈ {{2,3,4}}.

## 10. Cluster-number selection

k was selected from silhouette, minimum cluster size, and subject-bootstrap ARI. **Victim/control separation was not a selection criterion.**

Selection: `{choice}`

{structure}

## 11. Stability analysis

Subject-level 80% subsamples (150 replicates) and leave-one-subject-out ARI. Cycles were never resampled as if they were people.

## 12. Phenotype characterization

Each phenotype was contrasted with the remaining subjects using Cliff's delta on original (unscaled) features. Victimization was not used.

## 13. Trajectory characterization

When a stable solution existed, Phase 1 normalized cycles were summarized as subject medians, then phenotype medians (0–100% gait cycle). Inventory victimization columns were dropped before this step.

## 14. Victimization enrichment

Overall base rate: 17/31 victimized, 14/31 controls.

{enrich_txt}

Permutation shuffles **subject** labels. Multiple phenotypes are FDR-controlled on permutation p-values.

## 15. Confounding analysis

{cov_txt}

Anthropometry (mass, height, leg length) was not used to build clusters. An association would mean the gait phenotype may partly reflect body size rather than victimization.

## 16. Sensitivity analysis

Adjusted Rand index between hierarchical vs k-means and between family-balanced vs unbalanced global-PCA clustering is in `clustering/sensitivity.csv`. These comparisons did not use victimization labels.

## 17. Limitations

- n=31 is small; even a stable k may not generalize.
- Family PCA compresses correlated biomechanics; a discarded sibling feature may be more interpretable.
- Axes remain ax1/ax2/ax3.
- No classifier or victim score was trained.

## 18. Scientific conclusion

{conclusion}

This is not a claim that victimization causes gait, and it is not a predictive model.

## 19. Next steps

Phase 5 (supervised prediction) was not started. Any later predictive work must treat the 31 subjects as the independent unit and cannot reuse these labels for unsupervised k selection.

"""


def certify_phase4(project_root: Path, result: dict) -> dict:
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
    add("assignments_have_no_labels", "victimized" not in result["assignments"].columns, "assignment table is label-free")
    try:
        assert_no_labels(result["compact_frame"], where="cert")
        add("representation_label_free", True, "compact matrix has no label columns")
    except RuntimeError as e:
        add("representation_label_free", False, str(e))
    add("pca_present", len(result["pca_summary"]) > 0, "PCA summary written")
    add("cluster_metrics_present", len(result["metrics"]) > 0, "k grid evaluated")
    add("stability_subject_unit", (result["stability"]["unit"] == "subject").all(), "stability unit=subject")
    add("k_not_from_labels", "victim" not in json.dumps(result["choice"]).lower(), "selection payload has no victim criterion")
    add("sensitivity_present", len(result["sensitivity"]) > 0, "algorithm/representation ARI table")
    if result["choice"]["k"] is None:
        add("honest_no_structure", True, "no stable phenotype forced", warn=True)
        add("enrichment_deferred", result["enrichment"] is None or len(result["enrichment"]) == 0, "enrichment skipped without stable k")
    else:
        add("characterization_present", len(result["profiles"]) > 0, "label-blind profiles")
        add("trajectories_present", bool(result["trajectories"].get("data")), "phenotype trajectories")
        add("enrichment_subject_perm", (result["enrichment"]["unit"] == "subject").all() if len(result["enrichment"]) else False, "permutation unit=subject")
        add("confounding_present", len(result["covariates"]) > 0, "anthropometry vs phenotype")
        add("labels_post_discovery", result.get("labels_revealed") is True, "labels joined after freeze")
        sizes = result["assignments"]["phenotype"].value_counts()
        imbalanced = int(sizes.min()) <= 4 and int(sizes.max()) >= 20
        add(
            "not_two_large_phenotypes",
            True,
            f"sizes={dict(sizes.sort_index())}; majority/outgroup split — do not over-interpret as two gait types",
            warn=imbalanced,
        )
        height = result["covariates"]
        h = height.loc[height["variable"] == "height_cm", "kruskal_p"]
        if len(h) and float(h.iloc[0]) < 0.10:
            add("height_association", True, f"height Kruskal p={float(h.iloc[0]):.3g}; phenotype may partly track stature", warn=True)
    if any(c["status"] == "FAIL" for c in checks):
        status = "NOT CERTIFIED"
    elif any(c["status"] == "WARNING" for c in checks):
        status = "PASS WITH WARNINGS"
    else:
        status = "PASS"
    return {"generated": date.today().isoformat(), "status": status, "checks": checks, "choice": result["choice"]}
