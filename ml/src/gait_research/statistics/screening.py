"""Label-independent quality screening of subject-level features."""

from __future__ import annotations

import numpy as np
import pandas as pd

META_COLS = {"subject_id", "n_cycles", "n_left_cycles", "n_right_cycles"}
EXCLUDE_SUFFIXES = ("__mean", "__std", "__cv", "__n")


def analysis_columns(df: pd.DataFrame) -> list[str]:
    """Default analysis set: *__median plus subject-level var_* and sym_*.

    Does not include mean/std/cv/n aggregations unless the column is a
    dedicated variability feature (var_*).
    """
    cols = []
    for c in df.columns:
        if c in META_COLS:
            continue
        if c.endswith(EXCLUDE_SUFFIXES):
            continue
        if c.endswith("__median") or c.startswith("var_") or c.startswith("sym_"):
            cols.append(c)
    return cols


def _near_constant(x: np.ndarray) -> bool:
    finite = x[np.isfinite(x)]
    if finite.size <= 1:
        return True
    if np.unique(np.round(finite, 12)).size <= 1:
        return True
    med = np.median(finite)
    iqr = np.subtract(*np.percentile(finite, [75, 25]))
    if abs(med) > 0 and iqr / abs(med) < 1e-8:
        return True
    if iqr == 0 and np.std(finite) < 1e-12:
        return True
    return False


def quality_screen(df: pd.DataFrame, columns: list[str], *, min_n: int = 31) -> tuple[pd.DataFrame, list[str]]:
    """Screen features without using any group label."""
    if "victimized" in df.columns:
        raise RuntimeError("quality_screen must not receive group labels")
    rows = []
    keep = []
    for col in columns:
        x = pd.to_numeric(df[col], errors="coerce").to_numpy(dtype=float)
        n_valid = int(np.isfinite(x).sum())
        n_unique = int(np.unique(x[np.isfinite(x)]).size) if n_valid else 0
        reasons = []
        if n_valid < min_n:
            reasons.append("insufficient_n")
        if not np.isfinite(x).any():
            reasons.append("all_invalid")
        if np.isinf(x).any():
            reasons.append("nonfinite")
        if n_unique <= 1:
            reasons.append("constant")
        if _near_constant(x):
            reasons.append("near_constant")
        passed = not reasons
        if passed:
            for prev in keep:
                prev_x = pd.to_numeric(df[prev], errors="coerce").to_numpy(dtype=float)
                same_mask = np.isfinite(x) & np.isfinite(prev_x)
                if np.array_equal(np.isfinite(x), np.isfinite(prev_x)) and np.allclose(
                    x[same_mask], prev_x[same_mask], rtol=0.0, atol=0.0, equal_nan=True
                ):
                    reasons.append(f"duplicated:{prev}")
                    passed = False
                    break
        if passed:
            keep.append(col)
        rows.append(
            {
                "feature": col,
                "n_valid": n_valid,
                "n_unique": n_unique,
                "passed": passed,
                "reasons": "|".join(reasons),
            }
        )
    return pd.DataFrame(rows), keep


def redundancy_clusters(df: pd.DataFrame, columns: list[str], *, rho: float = 0.90) -> tuple[pd.DataFrame, list[str]]:
    """Spearman |rho| connected components. Representative chosen without labels."""
    if "victimized" in df.columns:
        raise RuntimeError("redundancy_clusters must not receive group labels")
    if not columns:
        return pd.DataFrame(), []
    mat = df[columns].apply(pd.to_numeric, errors="coerce")
    corr = mat.corr(method="spearman").abs().fillna(0.0)
    n = len(columns)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        a, b = find(i), find(j)
        if a != b:
            parent[b] = a

    for i in range(n):
        for j in range(i + 1, n):
            if corr.iloc[i, j] >= rho:
                union(i, j)

    clusters: dict[int, list[int]] = {}
    for i in range(n):
        clusters.setdefault(find(i), []).append(i)

    def score(name: str) -> tuple:
        """Prefer ROM, non-phase, kinematic-like names; then higher IQR."""
        x = pd.to_numeric(df[name], errors="coerce")
        iqr = float(x.quantile(0.75) - x.quantile(0.25)) if x.notna().any() else 0.0
        rom = 0 if "_rom" in name else 1
        phase = 0 if "_phase_" not in name else 1
        length = len(name)
        return (rom, phase, -iqr, length)

    rows = []
    reps = []
    for cid, idxs in enumerate(sorted(clusters.values(), key=lambda v: min(v)), start=1):
        names = [columns[i] for i in idxs]
        names_sorted = sorted(names, key=score)
        rep = names_sorted[0]
        reps.append(rep)
        max_r = 0.0
        if len(idxs) > 1:
            sub = corr.loc[names, names]
            vals = sub.to_numpy()
            max_r = float(np.nanmax(np.where(np.eye(len(names), dtype=bool), np.nan, vals)))
        rows.append(
            {
                "cluster_id": cid,
                "representative": rep,
                "n_members": len(names),
                "members": "|".join(names_sorted),
                "max_abs_spearman": max_r,
            }
        )
    return pd.DataFrame(rows), reps
