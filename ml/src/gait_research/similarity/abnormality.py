"""P0.2 — Shared abnormality-set overlap (binary exceedance Jaccard).

Question
--------
Do victims share *which* pre-registered features fall outside the control
reference band, even if their continuous deviation directions (P0.1) do not align?

Primary statistic
-----------------
Mean pairwise Jaccard similarity among the 17 victim binary exceedance vectors.

Reference band
--------------
Per feature: 10th–90th percentile of the 14 CONTROL subjects only.
Exceedance = value < p10 or value > p90.

Null
----
Permute victim/control labels across subjects (≥999). Unit = subject.

Pre-registered feature list is locked in
results/similarity/p02_abnormality/preregistered_features.json before any real test.
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
BAND_LO = 10.0
BAND_HI = 90.0


def load_preregistered_features(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    feats = [str(x) for x in payload["features"]]
    if len(feats) < 10 or len(feats) > 40:
        raise RuntimeError(f"expected ~30 preregistered features, got {len(feats)}")
    if len(feats) != len(set(feats)):
        raise RuntimeError("duplicate preregistered features")
    return feats


def control_bands(X: np.ndarray, victim: np.ndarray, *, lo: float = BAND_LO, hi: float = BAND_HI) -> tuple[np.ndarray, np.ndarray]:
    """Return (p_lo, p_hi) per column from controls only."""
    X = np.asarray(X, dtype=float)
    victim = np.asarray(victim, dtype=bool)
    ctrl = X[~victim]
    if ctrl.shape[0] < 2:
        raise ValueError("need ≥2 controls for percentile band")
    p_lo = np.nanpercentile(ctrl, lo, axis=0)
    p_hi = np.nanpercentile(ctrl, hi, axis=0)
    return p_lo, p_hi


def exceedance_matrix(X: np.ndarray, p_lo: np.ndarray, p_hi: np.ndarray) -> np.ndarray:
    """Binary matrix: 1 if outside [p_lo, p_hi]. Non-finite → 0 (not counted as exceed)."""
    X = np.asarray(X, dtype=float)
    finite = np.isfinite(X)
    out = ((X < p_lo) | (X > p_hi)) & finite
    return out.astype(np.uint8)


def jaccard(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=bool).ravel()
    b = np.asarray(b, dtype=bool).ravel()
    inter = int(np.sum(a & b))
    union = int(np.sum(a | b))
    if union == 0:
        return 1.0  # both all-normal: identical empty abnormality sets
    return float(inter / union)


def mean_pairwise_jaccard(B: np.ndarray) -> float:
    B = np.asarray(B)
    n = B.shape[0]
    if n < 2:
        return float("nan")
    vals = []
    for i in range(n):
        for j in range(i + 1, n):
            vals.append(jaccard(B[i], B[j]))
    return float(np.mean(vals)) if vals else float("nan")


def pairwise_jaccard_matrix(B: np.ndarray) -> np.ndarray:
    B = np.asarray(B)
    n = B.shape[0]
    out = np.eye(n, dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            v = jaccard(B[i], B[j])
            out[i, j] = v
            out[j, i] = v
    return out


def feature_prevalence(B: np.ndarray) -> np.ndarray:
    return np.mean(B.astype(float), axis=0)


def feature_coexceedance_rate(B: np.ndarray) -> np.ndarray:
    """For each feature, mean over victim pairs of (both exceed that feature)."""
    B = np.asarray(B, dtype=bool)
    n, p = B.shape
    if n < 2:
        return np.full(p, np.nan)
    rates = np.zeros(p, dtype=float)
    n_pairs = n * (n - 1) / 2
    for j in range(p):
        col = B[:, j]
        both = 0
        for i in range(n):
            if not col[i]:
                continue
            both += int(np.sum(col[i + 1 :]))
        rates[j] = both / n_pairs
    return rates


def build_exceedance(
    X: np.ndarray,
    victim: np.ndarray,
    *,
    lo: float = BAND_LO,
    hi: float = BAND_HI,
) -> dict:
    p_lo, p_hi = control_bands(X, victim, lo=lo, hi=hi)
    B = exceedance_matrix(X, p_lo, p_hi)
    return {"B": B, "p_lo": p_lo, "p_hi": p_hi, "victim_prevalence": feature_prevalence(B[victim])}


def permute_mean_pairwise_jaccard(
    X: np.ndarray,
    victim: np.ndarray,
    *,
    n_perm: int = N_PERM_DEFAULT,
    seed: int = SEED,
    lo: float = BAND_LO,
    hi: float = BAND_HI,
) -> dict:
    """Subject-label permutation. Band is recomputed from the permuted 'controls'."""
    X = np.asarray(X, dtype=float)
    victim = np.asarray(victim, dtype=bool)
    n = X.shape[0]
    n_v = int(victim.sum())
    built = build_exceedance(X, victim, lo=lo, hi=hi)
    obs = mean_pairwise_jaccard(built["B"][victim])
    rng = np.random.default_rng(seed)
    null = np.empty(n_perm, dtype=float)
    idx = np.arange(n)
    for i in range(n_perm):
        pick = rng.choice(idx, size=n_v, replace=False)
        mask = np.zeros(n, dtype=bool)
        mask[pick] = True
        b = build_exceedance(X, mask, lo=lo, hi=hi)
        null[i] = mean_pairwise_jaccard(b["B"][mask])
    ge = int(np.sum(null >= obs - 1e-15)) if np.isfinite(obs) else n_perm
    p = (1 + ge) / (n_perm + 1)
    return {
        "observed": obs,
        "null": null,
        "null_mean": float(np.nanmean(null)),
        "null_sd": float(np.nanstd(null, ddof=1)),
        "null_p95": float(np.nanpercentile(null, 95)),
        "perm_p": float(p),
        "n_perm": n_perm,
        "unit": "subject",
        "alternative": "greater_mean_pairwise_jaccard",
        "bands": built,
    }


def bootstrap_mean_pairwise_jaccard(
    B_victims: np.ndarray,
    *,
    n_boot: int = N_BOOT_DEFAULT,
    seed: int = SEED,
    alpha: float = 0.05,
) -> dict:
    B = np.asarray(B_victims)
    n = B.shape[0]
    rng = np.random.default_rng(seed)
    stats = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        stats[b] = mean_pairwise_jaccard(B[idx])
    lo, hi = np.nanpercentile(stats, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {"ci_low": float(lo), "ci_high": float(hi), "n_boot": n_boot, "alpha": alpha}


def loso_mean_pairwise_jaccard(X: np.ndarray, victim: np.ndarray) -> dict:
    X = np.asarray(X, dtype=float)
    victim = np.asarray(victim, dtype=bool)
    built = build_exceedance(X, victim)
    obs = mean_pairwise_jaccard(built["B"][victim])
    sign0 = 0.0 if not np.isfinite(obs) or abs(obs) < 1e-12 else float(np.sign(obs))
    n = X.shape[0]
    vals = []
    same = 0
    # feature-rank stability among victims: top-5 prevalence features
    prev = feature_prevalence(built["B"][victim])
    top_full = set(np.argsort(-prev)[:5].tolist())
    top_agree = 0
    n_loso_ok = 0
    for i in range(n):
        keep = np.ones(n, dtype=bool)
        keep[i] = False
        v = victim[keep]
        if int(v.sum()) < 2 or int((~v).sum()) < 2:
            vals.append(float("nan"))
            continue
        b = build_exceedance(X[keep], v)
        s = mean_pairwise_jaccard(b["B"][v])
        vals.append(s)
        if sign0 == 0.0 or (np.isfinite(s) and np.sign(s) == sign0):
            same += 1
        prev_i = feature_prevalence(b["B"][v])
        top_i = set(np.argsort(-prev_i)[:5].tolist())
        # Jaccard of top-5 feature index sets
        inter = len(top_full & top_i)
        union = len(top_full | top_i) or 1
        if inter / union >= 0.6:
            top_agree += 1
        n_loso_ok += 1
    vals_a = np.asarray(vals, dtype=float)
    # Jaccard ∈ [0,1]: LOSO "pass" is whether the most-shared features stay stable
    # (top-5 prevalence Jaccard ≥ 0.6 in every valid leave-one-out fold).
    rank_pass = bool(n_loso_ok > 0 and top_agree == n_loso_ok and np.isfinite(obs))
    return {
        "full_observed": obs,
        "loso_values": vals_a,
        "loso_min": float(np.nanmin(vals_a)),
        "loso_max": float(np.nanmax(vals_a)),
        "loso_sign_agreement": float(same / n),
        "loso_pass": rank_pass,
        "top5_feature_rank_agreement": float(top_agree / n_loso_ok) if n_loso_ok else float("nan"),
        "top5_full_indices": sorted(top_full),
    }


def per_feature_coexceedance_permutation(
    X: np.ndarray,
    victim: np.ndarray,
    feature_names: list[str],
    *,
    n_perm: int = N_PERM_DEFAULT,
    seed: int = SEED,
) -> pd.DataFrame:
    """Elevated pairwise co-exceedance among victims per feature; BH-FDR."""
    X = np.asarray(X, dtype=float)
    victim = np.asarray(victim, dtype=bool)
    n = X.shape[0]
    n_v = int(victim.sum())
    built = build_exceedance(X, victim)
    obs_rate = feature_coexceedance_rate(built["B"][victim])
    prev = feature_prevalence(built["B"][victim])
    rng = np.random.default_rng(seed)
    null = np.empty((n_perm, X.shape[1]), dtype=float)
    idx = np.arange(n)
    for i in range(n_perm):
        pick = rng.choice(idx, size=n_v, replace=False)
        mask = np.zeros(n, dtype=bool)
        mask[pick] = True
        b = build_exceedance(X, mask)
        null[i] = feature_coexceedance_rate(b["B"][mask])
    rows = []
    raw_p = []
    for j, name in enumerate(feature_names):
        ge = int(np.sum(null[:, j] >= obs_rate[j] - 1e-15))
        p = (1 + ge) / (n_perm + 1)
        raw_p.append(p)
        rows.append(
            {
                "feature": name,
                "victim_prevalence": float(prev[j]),
                "victim_pairwise_coexceedance": float(obs_rate[j]),
                "null_mean_coexceedance": float(np.mean(null[:, j])),
                "raw_p": float(p),
                "band_lo": float(built["p_lo"][j]),
                "band_hi": float(built["p_hi"][j]),
            }
        )
    out = pd.DataFrame(rows)
    out["fdr_q"] = benjamini_hochberg(np.asarray(raw_p, dtype=float))
    out = out.sort_values("raw_p").reset_index(drop=True)
    return out


@dataclass
class AbnormalityResult:
    representation: str
    n_subjects: int
    n_victims: int
    n_controls: int
    n_features: int
    mean_pairwise_jaccard: float
    bootstrap_ci_low: float
    bootstrap_ci_high: float
    perm_p: float
    null_mean: float
    null_p95: float
    n_perm: int
    mean_victim_prevalence: float
    loso_pass: bool
    loso_sign_agreement: float
    top5_feature_rank_agreement: float
    n_features_fdr_le_0_10: int
    residualized: bool
    residual_covariates: tuple[str, ...]
    seed: int

    def to_dict(self) -> dict:
        return asdict(self)


def run_abnormality_overlap(
    X: np.ndarray,
    victim: np.ndarray,
    feature_names: list[str],
    *,
    representation: str = "preregistered_30",
    n_perm: int = N_PERM_DEFAULT,
    n_boot: int = N_BOOT_DEFAULT,
    seed: int = SEED,
    residualized: bool = False,
    residual_covariates: tuple[str, ...] = (),
) -> tuple[AbnormalityResult, dict]:
    if X.shape[1] != len(feature_names):
        raise ValueError("feature_names length must match X columns")
    victim = np.asarray(victim, dtype=bool)
    perm = permute_mean_pairwise_jaccard(X, victim, n_perm=n_perm, seed=seed)
    B = perm["bands"]["B"]
    boot = bootstrap_mean_pairwise_jaccard(B[victim], n_boot=n_boot, seed=seed)
    loso = loso_mean_pairwise_jaccard(X, victim)
    feat_tab = per_feature_coexceedance_permutation(X, victim, feature_names, n_perm=n_perm, seed=seed + 1)
    n_fdr = int((feat_tab["fdr_q"] <= 0.10).sum())
    prev = feature_prevalence(B[victim])

    summary = AbnormalityResult(
        representation=representation,
        n_subjects=int(X.shape[0]),
        n_victims=int(victim.sum()),
        n_controls=int((~victim).sum()),
        n_features=int(X.shape[1]),
        mean_pairwise_jaccard=float(perm["observed"]),
        bootstrap_ci_low=boot["ci_low"],
        bootstrap_ci_high=boot["ci_high"],
        perm_p=perm["perm_p"],
        null_mean=perm["null_mean"],
        null_p95=perm["null_p95"],
        n_perm=perm["n_perm"],
        mean_victim_prevalence=float(np.mean(prev)),
        loso_pass=loso["loso_pass"],
        loso_sign_agreement=loso["loso_sign_agreement"],
        top5_feature_rank_agreement=loso["top5_feature_rank_agreement"],
        n_features_fdr_le_0_10=n_fdr,
        residualized=residualized,
        residual_covariates=residual_covariates,
        seed=seed,
    )
    details = {
        "B": B,
        "p_lo": perm["bands"]["p_lo"],
        "p_hi": perm["bands"]["p_hi"],
        "jaccard_matrix": pairwise_jaccard_matrix(B),
        "perm_null": perm["null"],
        "feature_table": feat_tab,
        "loso": loso,
        "bootstrap": boot,
        "victim_prevalence": prev,
    }
    return summary, details
