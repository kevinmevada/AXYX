"""P0.3 — Shared waveform shape (amplitude-normalized).

Question
--------
Do victims share *shape/timing* of core gait curves after discarding ROM/amplitude?

Primary statistics (reported separately, never averaged)
--------------------------------------------------------
1. Mean over preregistered curves of mean pairwise Pearson among victims.
2. Mean over preregistered curves of mean pairwise DTW distance among victims
   (alternative: smaller distance = more similar).

Normalization
-------------
Per subject, per curve: z-score across the 101 phase points (zero mean, unit
variance). Explicitly discards amplitude; preserves shape/timing.

Null
----
Permute victim/control labels across subjects (≥999). Unit = subject.

Curve list locked in results/similarity/p03_shape/preregistered_curves.json
before any real test.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ..statistics.multiple_testing import benjamini_hochberg

SEED = 20260813
N_PERM_DEFAULT = 9999
N_BOOT_DEFAULT = 2000
N_PHASE = 101
AXIS_TO_IDX = {"ax1": 0, "ax2": 1, "ax3": 2}


def load_preregistered_curves(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    curves = list(payload["curves"])
    if len(curves) != int(payload["n_curves"]):
        raise RuntimeError("n_curves mismatch in preregistered_curves.json")
    if len(curves) < 8 or len(curves) > 20:
        raise RuntimeError(f"expected ~12 preregistered curves, got {len(curves)}")
    ids = [c["id"] for c in curves]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate preregistered curve ids")
    return curves


def zscore_curves(curves: np.ndarray, *, eps: float = 1e-12) -> np.ndarray:
    """Z-score each curve over time. curves: (n_subjects, n_curves, n_time)."""
    X = np.asarray(curves, dtype=float)
    mu = np.nanmean(X, axis=2, keepdims=True)
    sd = np.nanstd(X, axis=2, keepdims=True)
    sd = np.where(sd < eps, 1.0, sd)
    out = (X - mu) / sd
    out[~np.isfinite(out)] = 0.0
    return out


def residualize_curves(curves: np.ndarray, covariates: np.ndarray) -> np.ndarray:
    """Residualize each (curve, time) column across subjects on covariates."""
    X = np.asarray(curves, dtype=float)
    Z = np.asarray(covariates, dtype=float)
    if Z.ndim == 1:
        Z = Z[:, None]
    n, n_c, n_t = X.shape
    if Z.shape[0] != n:
        raise ValueError("covariate rows must match subjects")
    Z2 = Z.copy()
    for j in range(Z2.shape[1]):
        col = Z2[:, j]
        med = np.nanmedian(col)
        col[~np.isfinite(col)] = med if np.isfinite(med) else 0.0
        Z2[:, j] = col
    design = np.column_stack([np.ones(n), Z2])
    DtD_inv = np.linalg.pinv(design.T @ design)
    flat = X.reshape(n, n_c * n_t)
    out = np.empty_like(flat)
    for j in range(flat.shape[1]):
        y = flat[:, j].copy()
        if not np.isfinite(y).all():
            med = np.nanmedian(y)
            y[~np.isfinite(y)] = med if np.isfinite(med) else 0.0
        beta = DtD_inv @ (design.T @ y)
        out[:, j] = y - design @ beta
    return out.reshape(n, n_c, n_t)


def pearson_sim(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float).ravel()
    b = np.asarray(b, dtype=float).ravel()
    if a.size != b.size or a.size == 0:
        return float("nan")
    a = a - np.mean(a)
    b = b - np.mean(b)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na <= 0 or nb <= 0:
        return float("nan")
    return float(np.dot(a, b) / (na * nb))


def dtw_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Standard DTW with squared Euclidean local cost; returns sqrt(path cost)."""
    a = np.asarray(a, dtype=np.float64).ravel()
    b = np.asarray(b, dtype=np.float64).ravel()
    return float(_dtw_distance_numba(a, b))


try:
    from numba import njit

    @njit(cache=True)
    def _dtw_distance_numba(a: np.ndarray, b: np.ndarray) -> float:
        n = a.shape[0]
        m = b.shape[0]
        prev = np.empty(m + 1)
        cur = np.empty(m + 1)
        prev[0] = 0.0
        for j in range(1, m + 1):
            prev[j] = np.inf
        for i in range(1, n + 1):
            cur[0] = np.inf
            ai = a[i - 1]
            for j in range(1, m + 1):
                cost = (ai - b[j - 1]) * (ai - b[j - 1])
                cand = prev[j]
                if cur[j - 1] < cand:
                    cand = cur[j - 1]
                if prev[j - 1] < cand:
                    cand = prev[j - 1]
                cur[j] = cost + cand
            # swap
            tmp = prev
            prev = cur
            cur = tmp
        return float(np.sqrt(prev[m]))

except ImportError:  # pragma: no cover

    def _dtw_distance_numba(a: np.ndarray, b: np.ndarray) -> float:
        n, m = a.size, b.size
        D = np.full((n + 1, m + 1), np.inf, dtype=float)
        D[0, 0] = 0.0
        for i in range(1, n + 1):
            ai = a[i - 1]
            for j in range(1, m + 1):
                cost = (ai - b[j - 1]) ** 2
                D[i, j] = cost + min(D[i - 1, j], D[i, j - 1], D[i - 1, j - 1])
        return float(np.sqrt(D[n, m]))


def pairwise_pearson_matrix(curves_1d: np.ndarray) -> np.ndarray:
    """curves_1d: (n_subjects, n_time) for one curve."""
    X = np.asarray(curves_1d, dtype=float)
    n = X.shape[0]
    out = np.eye(n, dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            v = pearson_sim(X[i], X[j])
            out[i, j] = v
            out[j, i] = v
    return out


def pairwise_dtw_matrix(curves_1d: np.ndarray) -> np.ndarray:
    X = np.asarray(curves_1d, dtype=float)
    n = X.shape[0]
    out = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            v = dtw_distance(X[i], X[j])
            out[i, j] = v
            out[j, i] = v
    return out


def mean_pairwise_from_matrix(M: np.ndarray, mask: np.ndarray) -> float:
    idx = np.where(mask)[0]
    if idx.size < 2:
        return float("nan")
    vals = []
    for a in range(idx.size):
        for b in range(a + 1, idx.size):
            vals.append(M[idx[a], idx[b]])
    vals = np.asarray(vals, dtype=float)
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return float("nan")
    return float(np.mean(vals))


def build_pairwise_banks(Z: np.ndarray) -> dict:
    """Precompute pairwise Pearson and DTW for every curve. Z: (n, n_curves, T)."""
    Z = np.asarray(Z, dtype=float)
    n_c = Z.shape[1]
    pearson = []
    dtw = []
    for c in range(n_c):
        pearson.append(pairwise_pearson_matrix(Z[:, c, :]))
        dtw.append(pairwise_dtw_matrix(Z[:, c, :]))
    return {"pearson": pearson, "dtw": dtw}


def aggregate_victim_stats(banks: dict, victim: np.ndarray) -> dict:
    victim = np.asarray(victim, dtype=bool)
    pear_per = np.array([mean_pairwise_from_matrix(M, victim) for M in banks["pearson"]], dtype=float)
    dtw_per = np.array([mean_pairwise_from_matrix(M, victim) for M in banks["dtw"]], dtype=float)
    return {
        "pearson_per_curve": pear_per,
        "dtw_per_curve": dtw_per,
        "mean_pairwise_pearson": float(np.nanmean(pear_per)),
        "mean_pairwise_dtw": float(np.nanmean(dtw_per)),
    }


def permute_shape_stats(
    banks: dict,
    victim: np.ndarray,
    *,
    n_perm: int = N_PERM_DEFAULT,
    seed: int = SEED,
) -> dict:
    victim = np.asarray(victim, dtype=bool)
    n = victim.size
    n_v = int(victim.sum())
    obs = aggregate_victim_stats(banks, victim)
    rng = np.random.default_rng(seed)
    null_p = np.empty(n_perm, dtype=float)
    null_d = np.empty(n_perm, dtype=float)
    null_p_curve = np.empty((n_perm, len(banks["pearson"])), dtype=float)
    null_d_curve = np.empty((n_perm, len(banks["dtw"])), dtype=float)
    idx = np.arange(n)
    for i in range(n_perm):
        pick = rng.choice(idx, size=n_v, replace=False)
        mask = np.zeros(n, dtype=bool)
        mask[pick] = True
        s = aggregate_victim_stats(banks, mask)
        null_p[i] = s["mean_pairwise_pearson"]
        null_d[i] = s["mean_pairwise_dtw"]
        null_p_curve[i] = s["pearson_per_curve"]
        null_d_curve[i] = s["dtw_per_curve"]

    # Pearson: greater similarity; DTW: smaller distance
    ge_p = int(np.sum(null_p >= obs["mean_pairwise_pearson"] - 1e-15))
    le_d = int(np.sum(null_d <= obs["mean_pairwise_dtw"] + 1e-15))
    return {
        "observed_pearson": obs["mean_pairwise_pearson"],
        "observed_dtw": obs["mean_pairwise_dtw"],
        "pearson_per_curve": obs["pearson_per_curve"],
        "dtw_per_curve": obs["dtw_per_curve"],
        "null_pearson": null_p,
        "null_dtw": null_d,
        "null_pearson_per_curve": null_p_curve,
        "null_dtw_per_curve": null_d_curve,
        "perm_p_pearson": float((1 + ge_p) / (n_perm + 1)),
        "perm_p_dtw": float((1 + le_d) / (n_perm + 1)),
        "null_mean_pearson": float(np.nanmean(null_p)),
        "null_mean_dtw": float(np.nanmean(null_d)),
        "null_p95_pearson": float(np.nanpercentile(null_p, 95)),
        "null_p05_dtw": float(np.nanpercentile(null_d, 5)),
        "n_perm": n_perm,
        "unit": "subject",
    }


def bootstrap_mean_pairwise(
    banks: dict,
    victim: np.ndarray,
    *,
    n_boot: int = N_BOOT_DEFAULT,
    seed: int = SEED,
    alpha: float = 0.05,
) -> dict:
    victim = np.asarray(victim, dtype=bool)
    v_idx = np.where(victim)[0]
    n_v = v_idx.size
    rng = np.random.default_rng(seed)
    bp = np.empty(n_boot, dtype=float)
    bd = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        # resample victim rows; build a pseudo-mask over full n by picking with replacement
        # Use direct mean over resampled pairs from victim submatrix
        pick = rng.choice(v_idx, size=n_v, replace=True)
        pear_vals = []
        dtw_vals = []
        for c, Mp in enumerate(banks["pearson"]):
            Md = banks["dtw"][c]
            pv, dv = [], []
            for i in range(n_v):
                for j in range(i + 1, n_v):
                    pv.append(Mp[pick[i], pick[j]])
                    dv.append(Md[pick[i], pick[j]])
            pear_vals.append(float(np.nanmean(pv)))
            dtw_vals.append(float(np.nanmean(dv)))
        bp[b] = float(np.nanmean(pear_vals))
        bd[b] = float(np.nanmean(dtw_vals))
    plo, phi = np.nanpercentile(bp, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    dlo, dhi = np.nanpercentile(bd, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {
        "pearson_ci_low": float(plo),
        "pearson_ci_high": float(phi),
        "dtw_ci_low": float(dlo),
        "dtw_ci_high": float(dhi),
        "n_boot": n_boot,
        "alpha": alpha,
    }


def loso_shape_stats(banks: dict, victim: np.ndarray) -> dict:
    victim = np.asarray(victim, dtype=bool)
    n = victim.size
    obs = aggregate_victim_stats(banks, victim)
    sign_p = 0.0 if not np.isfinite(obs["mean_pairwise_pearson"]) else float(np.sign(obs["mean_pairwise_pearson"]))
    # DTW: track whether LOSO stays on the same side of null later; here track stability of value
    pear_vals = []
    dtw_vals = []
    same_sign = 0
    n_ok = 0
    for i in range(n):
        keep = np.ones(n, dtype=bool)
        keep[i] = False
        v = victim & keep
        if int(v.sum()) < 2:
            pear_vals.append(float("nan"))
            dtw_vals.append(float("nan"))
            continue
        # drop subject i from pairwise banks by masking
        s = aggregate_victim_stats(banks, v)
        # but banks still include dropped subject's rows — mean_pairwise_from_matrix
        # only uses masked indices, so OK (dropped subject never selected if not victim,
        # and if victim dropped they're not in mask)
        pear_vals.append(s["mean_pairwise_pearson"])
        dtw_vals.append(s["mean_pairwise_dtw"])
        if sign_p == 0.0 or (np.isfinite(s["mean_pairwise_pearson"]) and np.sign(s["mean_pairwise_pearson"]) == sign_p):
            same_sign += 1
        n_ok += 1
    pear_a = np.asarray(pear_vals, dtype=float)
    dtw_a = np.asarray(dtw_vals, dtype=float)
    # LOSO pass: Pearson sign stable across all folds (DTW always positive distance)
    return {
        "full_pearson": obs["mean_pairwise_pearson"],
        "full_dtw": obs["mean_pairwise_dtw"],
        "loso_pearson": pear_a,
        "loso_dtw": dtw_a,
        "loso_pearson_min": float(np.nanmin(pear_a)),
        "loso_pearson_max": float(np.nanmax(pear_a)),
        "loso_dtw_min": float(np.nanmin(dtw_a)),
        "loso_dtw_max": float(np.nanmax(dtw_a)),
        "loso_sign_agreement": float(same_sign / n) if n else float("nan"),
        "loso_pass": bool(same_sign == n and np.isfinite(obs["mean_pairwise_pearson"])),
    }


def per_curve_table(
    perm: dict,
    curve_ids: list[str],
) -> pd.DataFrame:
    """Per-curve Pearson (greater) and DTW (less) vs null; BH-FDR within each family."""
    n_perm = perm["n_perm"]
    rows = []
    raw_p_pear = []
    raw_p_dtw = []
    for j, cid in enumerate(curve_ids):
        obs_p = float(perm["pearson_per_curve"][j])
        obs_d = float(perm["dtw_per_curve"][j])
        null_p = perm["null_pearson_per_curve"][:, j]
        null_d = perm["null_dtw_per_curve"][:, j]
        ge = int(np.sum(null_p >= obs_p - 1e-15))
        le = int(np.sum(null_d <= obs_d + 1e-15))
        pp = (1 + ge) / (n_perm + 1)
        pd_ = (1 + le) / (n_perm + 1)
        raw_p_pear.append(pp)
        raw_p_dtw.append(pd_)
        rows.append(
            {
                "curve": cid,
                "mean_pairwise_pearson": obs_p,
                "null_mean_pearson": float(np.mean(null_p)),
                "raw_p_pearson": float(pp),
                "mean_pairwise_dtw": obs_d,
                "null_mean_dtw": float(np.mean(null_d)),
                "raw_p_dtw": float(pd_),
            }
        )
    out = pd.DataFrame(rows)
    out["fdr_q_pearson"] = benjamini_hochberg(np.asarray(raw_p_pear, dtype=float))
    out["fdr_q_dtw"] = benjamini_hochberg(np.asarray(raw_p_dtw, dtype=float))
    return out.sort_values("raw_p_pearson").reset_index(drop=True)


@dataclass
class ShapeSpaceResult:
    representation: str
    n_subjects: int
    n_victims: int
    n_controls: int
    n_curves: int
    normalization: str
    mean_pairwise_pearson: float
    pearson_ci_low: float
    pearson_ci_high: float
    perm_p_pearson: float
    null_mean_pearson: float
    null_p95_pearson: float
    mean_pairwise_dtw: float
    dtw_ci_low: float
    dtw_ci_high: float
    perm_p_dtw: float
    null_mean_dtw: float
    null_p05_dtw: float
    n_perm: int
    loso_pass: bool
    loso_sign_agreement: float
    n_curves_pearson_fdr_le_0_10: int
    n_curves_dtw_fdr_le_0_10: int
    residualized: bool
    residual_covariates: tuple[str, ...]
    seed: int

    def to_dict(self) -> dict:
        return asdict(self)


def run_shape_space(
    curves: np.ndarray,
    victim: np.ndarray,
    curve_ids: list[str],
    *,
    representation: str = "phase1_zscored_core_curves",
    n_perm: int = N_PERM_DEFAULT,
    n_boot: int = N_BOOT_DEFAULT,
    seed: int = SEED,
    residualized: bool = False,
    residual_covariates: tuple[str, ...] = (),
    already_zscored: bool = False,
) -> tuple[ShapeSpaceResult, dict]:
    """curves: (n_subjects, n_curves, 101) raw or already z-scored."""
    if curves.shape[1] != len(curve_ids):
        raise ValueError("curve_ids length must match curves")
    if curves.shape[2] != N_PHASE:
        raise ValueError(f"expected {N_PHASE} phase points")
    victim = np.asarray(victim, dtype=bool)
    Z = curves if already_zscored else zscore_curves(curves)
    banks = build_pairwise_banks(Z)
    perm = permute_shape_stats(banks, victim, n_perm=n_perm, seed=seed)
    boot = bootstrap_mean_pairwise(banks, victim, n_boot=n_boot, seed=seed)
    loso = loso_shape_stats(banks, victim)
    curve_tab = per_curve_table(perm, curve_ids)
    n_fdr_p = int((curve_tab["fdr_q_pearson"] <= 0.10).sum())
    n_fdr_d = int((curve_tab["fdr_q_dtw"] <= 0.10).sum())

    summary = ShapeSpaceResult(
        representation=representation,
        n_subjects=int(curves.shape[0]),
        n_victims=int(victim.sum()),
        n_controls=int((~victim).sum()),
        n_curves=int(curves.shape[1]),
        normalization="zscore_across_101_phase_points",
        mean_pairwise_pearson=perm["observed_pearson"],
        pearson_ci_low=boot["pearson_ci_low"],
        pearson_ci_high=boot["pearson_ci_high"],
        perm_p_pearson=perm["perm_p_pearson"],
        null_mean_pearson=perm["null_mean_pearson"],
        null_p95_pearson=perm["null_p95_pearson"],
        mean_pairwise_dtw=perm["observed_dtw"],
        dtw_ci_low=boot["dtw_ci_low"],
        dtw_ci_high=boot["dtw_ci_high"],
        perm_p_dtw=perm["perm_p_dtw"],
        null_mean_dtw=perm["null_mean_dtw"],
        null_p05_dtw=perm["null_p05_dtw"],
        n_perm=perm["n_perm"],
        loso_pass=loso["loso_pass"],
        loso_sign_agreement=loso["loso_sign_agreement"],
        n_curves_pearson_fdr_le_0_10=n_fdr_p,
        n_curves_dtw_fdr_le_0_10=n_fdr_d,
        residualized=residualized,
        residual_covariates=residual_covariates,
        seed=seed,
    )
    details = {
        "Z": Z,
        "banks": banks,
        "perm": perm,
        "bootstrap": boot,
        "loso": loso,
        "curve_table": curve_tab,
    }
    return summary, details
