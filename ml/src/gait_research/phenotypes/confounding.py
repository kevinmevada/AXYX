"""Anthropometric association with frozen phenotypes. Not used to build clusters."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kruskal

COVARIATE_COLS = ("mass_kg", "height_cm", "lleg_cm", "rleg_cm")


def load_covariates(project_root: Path) -> pd.DataFrame:
    path = project_root / "results" / "phase0" / "subject_inventory.csv"
    raw = pd.read_csv(path)
    keep = ["subject_id", *COVARIATE_COLS]
    missing = [c for c in keep if c not in raw.columns]
    if missing:
        raise RuntimeError(f"missing covariates: {missing}")
    out = raw[keep].copy()
    return out


def phenotype_covariates(assignments: pd.DataFrame, cov: pd.DataFrame) -> pd.DataFrame:
    df = assignments.merge(cov, on="subject_id", how="left")
    rows = []
    for col in COVARIATE_COLS:
        grouped = []
        summaries = []
        for ph, g in df.groupby("phenotype"):
            x = pd.to_numeric(g[col], errors="coerce").to_numpy(dtype=float)
            x = x[np.isfinite(x)]
            grouped.append(x)
            summaries.append(
                {
                    "variable": col,
                    "phenotype": int(ph),
                    "n": int(x.size),
                    "median": float(np.median(x)) if x.size else float("nan"),
                    "mean": float(np.mean(x)) if x.size else float("nan"),
                }
            )
        usable = [g for g in grouped if g.size >= 2]
        if len(usable) >= 2:
            try:
                stat, p = kruskal(*usable)
            except ValueError:
                stat, p = float("nan"), float("nan")
        else:
            stat, p = float("nan"), float("nan")
        for row in summaries:
            row["kruskal_h"] = float(stat) if stat == stat else float("nan")
            row["kruskal_p"] = float(p) if p == p else float("nan")
            rows.append(row)
    return pd.DataFrame(rows)
