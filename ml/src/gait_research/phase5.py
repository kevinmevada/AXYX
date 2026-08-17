"""Phase 5 writers, figures, report, certification. Does not modify Phases 0–4."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .phenotypes.representation import assert_no_labels


def _dirs(root: Path) -> dict[str, Path]:
    base = root / "results" / "phase5"
    paths = {
        "base": base,
        "similarity": base / "similarity",
        "subgroups": base / "subgroups",
        "neighbors": base / "neighbors",
        "vs_controls": base / "vs_controls",
        "characterization": base / "characterization",
        "confounding": base / "confounding",
        "figures": base / "figures",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def write_phase5(project_root: Path, result: dict) -> None:
    d = _dirs(project_root)
    sim = dict(result["similarity"])
    pd.DataFrame([{**sim, **result["gap"]}]).to_csv(d["similarity"] / "within_victim_similarity.csv", index=False)
    pd.DataFrame({"null_mean_pairwise_distance": result["similarity_null"]}).to_csv(
        d["similarity"] / "permutation_null.csv", index=False
    )
    result["nn_table"].to_csv(d["neighbors"] / "nearest_neighbors.csv", index=False)
    pd.DataFrame([result["nn_perm"]]).to_csv(d["neighbors"] / "nn_permutation.csv", index=False)
    sub = result["subgroups"]
    sub["assignments"].to_csv(d["subgroups"] / "assignments.csv", index=False)
    sub["assignments"].to_csv(d["base"] / "victim_subgroup_assignments.csv", index=False)
    sub["metrics"].to_csv(d["subgroups"] / "cluster_metrics.csv", index=False)
    sub["stability"].to_csv(d["subgroups"] / "cluster_stability.csv", index=False)
    result["vs_controls_compact"].to_csv(d["vs_controls"] / "subgroup_vs_control.csv", index=False)
    pd.DataFrame([result["all_victims_vs_controls"]]).to_csv(d["vs_controls"] / "all_victims_vs_control.csv", index=False)
    result["vs_controls_features"].head(500).to_csv(d["vs_controls"] / "subgroup_vs_control_features.csv", index=False)
    result["profiles"].to_csv(d["characterization"] / "subgroup_profiles.csv", index=False)
    result["vs_other_victims"].head(500).to_csv(d["characterization"] / "subgroup_vs_other_victims.csv", index=False)
    result["anatomy"].to_csv(d["characterization"] / "anatomical_summary.csv", index=False)
    result["phase_effects"].to_csv(d["characterization"] / "phase_effects.csv", index=False)
    result["covariates"].to_csv(d["confounding"] / "subgroup_covariates.csv", index=False)
    (d["subgroups"] / "selection.json").write_text(json.dumps(sub["choice"], indent=2, default=str), encoding="utf-8")

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(result["similarity_null"], bins=30, color="#8aa0a8", edgecolor="white")
    ax.axvline(sim["observed_mean_pairwise_distance"], color="#6b4c7a", lw=2, label="observed victims")
    ax.set_xlabel("Mean pairwise Euclidean distance")
    ax.set_title("Within-victim similarity vs random groups of 17")
    ax.legend()
    fig.tight_layout()
    fig.savefig(d["figures"] / "within_victim_similarity.png", dpi=140)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 5))
    vmask = result["y"] == "Y"
    ax.scatter(result["X"][~vmask, 0], result["X"][~vmask, 1], c="#bbbbbb", s=32, label="control")
    assign = sub["assignments"]
    for sg, g in assign.groupby("subgroup"):
        keep = np.array([sid in set(g["subject_id"]) for sid in result["ids"]])
        ax.scatter(result["X"][keep, 0], result["X"][keep, 1], s=44, label=f"victim SG {sg}")
    ax.set_xlabel("Family PC 1")
    ax.set_ylabel("Family PC 2")
    ax.set_title("Victims in Phase 4 gait space")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(d["figures"] / "victim_space.png", dpi=140)
    plt.close(fig)

    if len(result["vs_controls_compact"]):
        fig, ax = plt.subplots(figsize=(5, 4))
        vc = result["vs_controls_compact"]
        ax.bar(vc["subgroup"].astype(str), vc["centroid_distance"], color="#4a4a4a")
        ax.set_xlabel("Victim subgroup")
        ax.set_ylabel("Centroid distance to controls")
        ax.set_title("Subgroup vs 14 controls (compact gait space)")
        fig.tight_layout()
        fig.savefig(d["figures"] / "subgroup_vs_control.png", dpi=140)
        plt.close(fig)

    (d["base"] / "phase5_report.md").write_text(render_phase5_report(result), encoding="utf-8")


def render_phase5_report(result: dict) -> str:
    sim = result["similarity"]
    sub = result["subgroups"]
    k = sub["choice"]["k"]
    nn = result["nn_perm"]
    if k is None:
        sizes = "none"
        n_stable = 0
        vs = "No stable victim subgroups, so subgroup-vs-control tests were not interpreted."
        conclusion = (
            "No robust within-victim gait structure was detected. Victims are not more similar to each other "
            "than random groups of 17 in the certified gait representation, or any candidate split failed "
            "stability/size rules. This does not revive a population-wide victim signature."
        )
        if sim["perm_p"] <= 0.05:
            conclusion = (
                "Victims show greater within-group similarity than random subject sets of size 17, but no "
                "stable discrete subgroups met the pre-specified clustering rules. Treat this as a weak "
                "homogeneity signal, not a diagnostic subtype."
            )
    else:
        sizes = dict(sub["assignments"]["subgroup"].value_counts().sort_index())
        n_stable = int(sub["choice"]["k"])
        lines = []
        for r in result["vs_controls_compact"].itertuples():
            flag = "YES" if r.different_from_controls else "NO"
            lines.append(
                f"- Subgroup {int(r.subgroup)} (n={int(r.n_subgroup)}): centroid distance={r.centroid_distance:.3f}, "
                f"perm p={r.perm_p:.3g}, FDR q={r.fdr_q:.3g}, different from controls={flag}"
            )
        vs = "\n".join(lines) if lines else "No compact-space tests."
        any_diff = bool(len(result["vs_controls_compact"]) and result["vs_controls_compact"]["different_from_controls"].any())
        conclusion = (
            f"A k={k} victim-only partition met stability rules (sizes {sizes}). "
            + (
                "At least one subgroup differed from the 14 controls after subject-level permutation and FDR."
                if any_diff
                else "No subgroup was distinguishable from the 14 controls after subject-level permutation and FDR."
            )
        )
        if sim["perm_p"] > 0.05:
            conclusion += " Overall within-victim similarity was not greater than chance."

    top_txt = "Not applicable."
    if len(result["profiles"]):
        bits = []
        for r in result["profiles"].head(12).itertuples():
            bits.append(f"- SG{int(r.subgroup)} `{r.feature}` {r.direction} δ={r.cliffs_delta:.2f} ({r.anatomical_region})")
        top_txt = "\n".join(bits)
    ana_txt = "Not applicable."
    if len(result["anatomy"]):
        ana_txt = result["anatomy"].head(12).to_string(index=False)
    ph_txt = "Not applicable."
    if len(result["phase_effects"]):
        tmp = result["phase_effects"].copy()
        tmp["abs_d"] = tmp["cliffs_delta"].abs()
        agg = tmp.groupby("phase_mid")["abs_d"].median().sort_index()
        ph_txt = ", ".join(f"{int(m)}%:{v:.2f}" for m, v in agg.items())
    cov_txt = "Not applicable."
    if len(result["covariates"]):
        pvals = result["covariates"].drop_duplicates(["variable"])[["variable", "kruskal_p"]]
        cov_txt = ", ".join(f"{a} p={b:.3g}" for a, b in pvals.itertuples(index=False))

    return f"""# Phase 5 Within-Victim Gait Similarity and Subgroup Discovery

Generated: {date.today().isoformat()}

## Objective

Phase 3 found no shared victim-versus-control signature. Phase 4 found no victim-enriched population phenotypes.
Phase 5 asks whether the **17 victimized subjects** are more similar to each other than chance, and whether they form stable gait subgroups that differ from the **14 controls**.

Independent unit: **subject** (n=31; 17 victimized). Cycles were not clustering units.

The gait representation is the certified Phase 4 family-balanced compact matrix (31 × {result['rep']['compact'].shape[1]}), built without victimization in scaling, PCA, or feature selection. Labels were used only to subset victims and to test similarity/enrichment.

## Within-victim similarity

- Observed mean pairwise distance (17 victims): **{sim['observed_mean_pairwise_distance']:.4f}**
- Permutation null mean (random 17 of 31): **{sim['null_mean']:.4f}** (SD {sim['null_sd']:.4f}; 5th–95th {sim['null_p05']:.4f}–{sim['null_p95']:.4f})
- Permutation p (more similar than chance): **{sim['perm_p']:.4g}**
- Permutations: {sim['n_perm']}, unit={sim['unit']}
- Victim–victim / control–control / victim–control mean pairwise: {result['gap']['mean_pairwise_victim_victim']:.4f} / {result['gap']['mean_pairwise_control_control']:.4f} / {result['gap']['mean_pairwise_victim_control']:.4f}

## Nearest neighbors

- Fraction of victims whose 1-NN is another victim: **{nn['obs_frac_nn_victim']:.3f}** (null mean {nn['null_mean']:.3f}, perm p={nn['perm_p']:.3g})
- Mean 3-NN victim fraction: **{nn['knn3_victim_fraction']:.3f}**

## Victim subgroups

- Selected k: **{k}**
- Reason: `{sub['choice']['reason']}`
- Number of stable subgroups: **{0 if k is None else k}**
- Sizes: {sizes}
- Leave-one-**victim**-out mean ARI: **{sub['loso_ari']}**

k was chosen from silhouette, minimum size, and victim-level bootstrap ARI — not from victim-versus-control separation.

## All 17 victims vs 14 controls (compact space)

Centroid distance={result['all_victims_vs_controls']['centroid_distance']:.4f}, perm p={result['all_victims_vs_controls']['perm_p']:.3g}.

## Subgroup vs controls

{vs}

## Strongest biomechanical characteristics (subgroup vs other victims)

{top_txt}

## Anatomical regions

{ana_txt}

## Gait phases (median |δ| by bin midpoint, subgroup vs controls)

{ph_txt}

## Confounding

{cov_txt}

## Limitations

- n=17 is small; a 4-person split can be an outlier set.
- Compact space was estimated on all 31 subjects (gait-only, label-blind features).
- No classifier, victim score, or causal claim.

## Scientific conclusion

{conclusion}

Phase 6 was not started.
"""


def certify_phase5(result: dict) -> dict:
    checks = []

    def add(name, ok, detail, warn=False):
        if not ok:
            st = "FAIL"
        elif warn:
            st = "WARNING"
        else:
            st = "PASS"
        checks.append({"name": name, "status": st, "detail": detail})

    add("n_victims_17", result["n_victims"] == 17, f"n_victims={result['n_victims']}")
    add("n_controls_14", result["n_controls"] == 14, f"n_controls={result['n_controls']}")
    add("n_subjects_31", result["n_subjects"] == 31, "subject-level representation")
    add("perm_unit_subject", result["similarity"]["unit"] == "subject", "similarity permutation unit=subject")
    add("nn_perm_unit_subject", result["nn_perm"]["unit"] == "subject", "NN permutation unit=subject")
    add("assignments_no_label_col", "victimized" not in result["subgroups"]["assignments"].columns, "assignment table has no victimized column")
    try:
        assert_no_labels(pd.DataFrame(result["rep"]["compact"], columns=result["rep"]["compact_names"]))
        add("representation_gait_only", True, "compact gait matrix has no label columns")
    except RuntimeError as e:
        add("representation_gait_only", False, str(e))
    add("similarity_p_present", np.isfinite(result["similarity"]["perm_p"]), "within-victim p reported")
    k = result["subgroups"]["choice"]["k"]
    if k is None:
        add("honest_no_subgroup", True, "no stable victim subgroup forced", warn=True)
    else:
        add("loso_present", np.isfinite(result["subgroups"]["loso_ari"]), f"LOVO ARI={result['subgroups']['loso_ari']:.3f}")
        add("vs_control_present", len(result["vs_controls_compact"]) > 0, "subgroup vs control tests")
        add("vs_control_unit", (result["vs_controls_compact"]["unit"] == "subject").all(), "vs-control permutation unit=subject")
        add("confounding_present", len(result["covariates"]) > 0, "anthropometry on victim subgroups")
    if any(c["status"] == "FAIL" for c in checks):
        status = "NOT CERTIFIED"
    elif any(c["status"] == "WARNING" for c in checks):
        status = "PASS WITH WARNINGS"
    else:
        status = "PASS"
    return {"generated": date.today().isoformat(), "status": status, "checks": checks, "choice": result["subgroups"]["choice"]}
