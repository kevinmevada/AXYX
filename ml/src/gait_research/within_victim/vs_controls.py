"""Subgroup vs control tests after victim subgroups are frozen."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..statistics.effect_sizes import cliffs_delta, cliffs_delta_label
from ..statistics.multiple_testing import benjamini_hochberg

SEED = 20260813
N_PERM = 999


def centroid_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a.mean(axis=0) - b.mean(axis=0)))


def centroid_perm_p(
    x_sub: np.ndarray,
    x_ctrl: np.ndarray,
    *,
    n_perm: int = N_PERM,
    seed: int = SEED,
) -> tuple[float, float]:
    obs = centroid_distance(x_sub, x_ctrl)
    pooled = np.vstack([x_sub, x_ctrl])
    n_s = x_sub.shape[0]
    rng = np.random.default_rng(seed)
    ge = 0
    for _ in range(n_perm):
        idx = rng.permutation(len(pooled))
        a = pooled[idx[:n_s]]
        b = pooled[idx[n_s:]]
        if centroid_distance(a, b) >= obs - 1e-15:
            ge += 1
    p = (1 + ge) / (n_perm + 1)
    return obs, float(p)


def subgroup_vs_control_compact(
    X: np.ndarray,
    subject_id: np.ndarray,
    victimized: np.ndarray,
    assign: pd.DataFrame,
    *,
    seed: int = SEED,
) -> pd.DataFrame:
    id_to_i = {s: i for i, s in enumerate(subject_id)}
    ctrl = X[victimized == "N"]
    rows = []
    for sg, g in assign.groupby("subgroup"):
        if str(sg) == "none_stable":
            continue
        idx = [id_to_i[s] for s in g["subject_id"]]
        xs = X[idx]
        dist, p = centroid_perm_p(xs, ctrl, seed=seed)
        rows.append(
            {
                "subgroup": int(sg),
                "n_subgroup": int(len(idx)),
                "n_controls": int(ctrl.shape[0]),
                "centroid_distance": dist,
                "perm_p": p,
                "n_perm": N_PERM,
                "unit": "subject",
                "test": "centroid_distance_subgroup_vs_controls",
            }
        )
    out = pd.DataFrame(rows)
    if len(out):
        out["fdr_q"] = benjamini_hochberg(out["perm_p"].to_numpy())
        out["different_from_controls"] = (out["fdr_q"] <= 0.05) & (out["n_subgroup"] >= 4)
    return out


def subgroup_vs_control_features(
    raw: np.ndarray,
    names: list[str],
    meta: pd.DataFrame,
    subject_id: np.ndarray,
    victimized: np.ndarray,
    assign: pd.DataFrame,
) -> pd.DataFrame:
    id_to_i = {s: i for i, s in enumerate(subject_id)}
    ctrl_idx = [i for i, y in enumerate(victimized) if y == "N"]
    ctrl = raw[ctrl_idx]
    rows = []
    for sg, g in assign.groupby("subgroup"):
        if str(sg) == "none_stable":
            continue
        idx = [id_to_i[s] for s in g["subject_id"]]
        xs = raw[idx]
        for j, name in enumerate(names):
            a = xs[:, j]
            b = ctrl[:, j]
            a = a[np.isfinite(a)]
            b = b[np.isfinite(b)]
            delta = cliffs_delta(a, b)
            rows.append(
                {
                    "subgroup": int(sg),
                    "feature": name,
                    "n_subgroup": int(a.size),
                    "n_controls": int(b.size),
                    "median_subgroup": float(np.median(a)) if a.size else float("nan"),
                    "median_control": float(np.median(b)) if b.size else float("nan"),
                    "cliffs_delta": delta,
                    "cliffs_magnitude": cliffs_delta_label(delta),
                    "direction": (
                        "SUBGROUP_HIGHER" if delta > 0 else "SUBGROUP_LOWER" if delta < 0 else "TIED"
                    ),
                }
            )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.merge(meta, on="feature", how="left")
    df["abs_delta"] = df["cliffs_delta"].abs()
    return df.sort_values(["subgroup", "abs_delta"], ascending=[True, False]).reset_index(drop=True)
