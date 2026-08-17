"""Post-discovery victimization enrichment. Subject is the permutation unit."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

from ..statistics.multiple_testing import benjamini_hochberg

N_PERM = 999
SEED = 20260813


def composition_table(assignments: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    df = assignments.merge(labels, on="subject_id", how="left")
    if df["victimized"].isna().any():
        raise RuntimeError("label merge failed")
    rows = []
    n = len(df)
    n_y = int((df["victimized"] == "Y").sum())
    n_n = int((df["victimized"] == "N").sum())
    for ph, g in df.groupby("phenotype"):
        ny = int((g["victimized"] == "Y").sum())
        nn = int((g["victimized"] == "N").sum())
        table = np.array([[ny, nn], [n_y - ny, n_n - nn]], dtype=int)
        if table.min() >= 0 and table.sum() == n:
            _, p = fisher_exact(table, alternative="two-sided")
        else:
            p = float("nan")
        rows.append(
            {
                "phenotype": int(ph),
                "n_subjects": int(len(g)),
                "n_victimized": ny,
                "n_control": nn,
                "prop_victimized": ny / len(g) if len(g) else float("nan"),
                "prop_control": nn / len(g) if len(g) else float("nan"),
                "expected_prop_victimized": n_y / n if n else float("nan"),
                "fisher_p": float(p),
            }
        )
    return pd.DataFrame(rows)


def permutation_enrichment(
    assignments: pd.DataFrame,
    labels: pd.DataFrame,
    *,
    n_perm: int = N_PERM,
    seed: int = SEED,
) -> pd.DataFrame:
    df = assignments.merge(labels, on="subject_id", how="left")
    y = (df["victimized"] == "Y").to_numpy()
    ph = df["phenotype"].to_numpy()
    n_y = int(y.sum())
    n = len(df)
    expected = n_y / n
    rng = np.random.default_rng(seed)
    phenotypes = sorted(np.unique(ph))
    obs = {}
    for p in phenotypes:
        mask = ph == p
        obs[int(p)] = abs(float(y[mask].mean()) - expected)

    null_ge = {int(p): 0 for p in phenotypes}
    for _ in range(n_perm):
        shuf = rng.permutation(y)
        for p in phenotypes:
            mask = ph == p
            stat = abs(float(shuf[mask].mean()) - expected)
            if stat >= obs[int(p)] - 1e-15:
                null_ge[int(p)] += 1
    rows = []
    for p in phenotypes:
        pp = (1 + null_ge[int(p)]) / (n_perm + 1)
        rows.append(
            {
                "phenotype": int(p),
                "obs_abs_prop_diff": obs[int(p)],
                "perm_p": float(pp),
                "n_perm": n_perm,
                "unit": "subject",
            }
        )
    out = pd.DataFrame(rows)
    out["fdr_q"] = benjamini_hochberg(out["perm_p"].to_numpy())
    return out
