"""Label-blind biomechanical characterization of phenotypes."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..statistics.effect_sizes import cliffs_delta, cliffs_delta_label
from .representation import assert_no_labels


def phenotype_feature_effects(
    raw: np.ndarray,
    names: list[str],
    labels: np.ndarray,
    meta: pd.DataFrame,
) -> pd.DataFrame:
    """Each phenotype vs the remaining subjects. No victimization labels."""
    rows = []
    labs = np.asarray(labels)
    for ph in sorted(np.unique(labs)):
        inside = raw[labs == ph]
        outside = raw[labs != ph]
        for j, name in enumerate(names):
            a = inside[:, j]
            b = outside[:, j]
            a = a[np.isfinite(a)]
            b = b[np.isfinite(b)]
            delta = cliffs_delta(a, b)
            rows.append(
                {
                    "phenotype": int(ph),
                    "feature": name,
                    "n_in": int(a.size),
                    "n_out": int(b.size),
                    "median_in": float(np.median(a)) if a.size else float("nan"),
                    "median_out": float(np.median(b)) if b.size else float("nan"),
                    "cliffs_delta": delta,
                    "cliffs_magnitude": cliffs_delta_label(delta),
                    "direction": "HIGHER_IN_PHENOTYPE" if delta > 0 else "LOWER_IN_PHENOTYPE" if delta < 0 else "TIED",
                }
            )
    df = pd.DataFrame(rows)
    df = df.merge(meta, on="feature", how="left")
    df["abs_delta"] = df["cliffs_delta"].abs()
    df = df.sort_values(["phenotype", "abs_delta"], ascending=[True, False]).reset_index(drop=True)
    assert_no_labels(df, where="phenotype_features")
    return df


def phenotype_profiles(effects: pd.DataFrame, *, top_n: int = 8) -> pd.DataFrame:
    parts = []
    for ph, g in effects.groupby("phenotype"):
        top = g.head(top_n).copy()
        top["rank_in_phenotype"] = np.arange(1, len(top) + 1)
        parts.append(top)
    out = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    if len(out):
        assert_no_labels(out, where="phenotype_profiles")
    return out
