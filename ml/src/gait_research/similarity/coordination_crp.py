"""P0.6 — Shared inter-joint continuous relative phase (CRP) coupling.

Question
--------
Do victims share *coupling* between joints (CRP profiles) independent of each
joint's marginal position/timing/shape (what P0.1–P0.4 tested)?

CRP method
----------
Hilbert analytic-signal phase of the demeaned ax1 angle curve per joint.
CRP = wrap(φ_proximal − φ_distal) to (−π, π]. Angular velocity is not stored
in Phase 1 and is not required for Hilbert phase.

Similarity
----------
Reuse P0.3: Pearson and DTW on subject CRP profiles after unwrap(CRP−CRP[0])
and per-curve z-score. Report both; never average into one number.

Pairs locked in results/similarity/p06_coordination/preregistered_pairs.json.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import hilbert

from ..features.base import N_PHASE
from ..statistics.multiple_testing import benjamini_hochberg
from .shape_space import (
    SEED,
    N_BOOT_DEFAULT,
    N_PERM_DEFAULT,
    AXIS_TO_IDX,
    bootstrap_mean_pairwise,
    dtw_distance,
    loso_shape_stats,
    mean_pairwise_from_matrix,
    pairwise_dtw_matrix,
    permute_shape_stats,
    residualize_curves,
)


def load_preregistered_pairs(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    pairs = list(payload["pairs"])
    if len(pairs) != int(payload["n_pairs"]):
        raise RuntimeError("n_pairs mismatch")
    if int(payload["n_fdr_family"]) != len(pairs) * 2:
        raise RuntimeError("n_fdr_family must be n_pairs × 2 measures")
    return payload


def wrap_pi(x: np.ndarray) -> np.ndarray:
    """Wrap radians to (−π, π]."""
    return (np.asarray(x, dtype=float) + np.pi) % (2 * np.pi) - np.pi


def hilbert_phase(angle: np.ndarray) -> np.ndarray:
    """Instantaneous phase via Hilbert analytic signal of demeaned angle."""
    x = np.asarray(angle, dtype=float).ravel()
    if x.size != N_PHASE:
        raise ValueError(f"expected {N_PHASE} samples, got {x.size}")
    if not np.isfinite(x).all():
        x = x.copy()
        idx = np.arange(x.size)
        ok = np.isfinite(x)
        if ok.sum() < 8:
            return np.full(x.size, np.nan)
        x[~ok] = np.interp(idx[~ok], idx[ok], x[ok])
    x = x - np.mean(x)
    return np.angle(hilbert(x))


def continuous_relative_phase(proximal: np.ndarray, distal: np.ndarray) -> np.ndarray:
    """CRP = wrap(φ_prox − φ_dist) using Hilbert phases."""
    return wrap_pi(hilbert_phase(proximal) - hilbert_phase(distal))


def crp_similarity_profile(crp: np.ndarray) -> np.ndarray:
    """Unwrap relative to IC, for P0.3-style Pearson/DTW on a real curve."""
    c = np.asarray(crp, dtype=float).ravel()
    c = wrap_pi(c - c[0])
    return np.unwrap(c)


def circular_mean_crp(stack: np.ndarray) -> np.ndarray:
    """stack: (n_cycles, 101) wrapped CRP → circular mean across cycles."""
    stack = np.asarray(stack, dtype=float)
    s = np.nanmean(np.sin(stack), axis=0)
    c = np.nanmean(np.cos(stack), axis=0)
    return np.arctan2(s, c)


def circular_curve_sim(a: np.ndarray, b: np.ndarray) -> float:
    """mean_t cos(wrap(a−b)); 1 = identical CRP, sensitive to constant offsets."""
    return float(np.mean(np.cos(wrap_pi(np.asarray(a) - np.asarray(b)))))


def pairwise_circular_matrix(curves_1d: np.ndarray) -> np.ndarray:
    X = np.asarray(curves_1d, dtype=float)
    n = X.shape[0]
    out = np.eye(n, dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            v = circular_curve_sim(X[i], X[j])
            out[i, j] = v
            out[j, i] = v
    return out


def build_crp_banks(wrapped: np.ndarray) -> dict:
    """Circular similarity on wrapped CRP; DTW on unwrap(CRP−CRP[0])."""
    wrapped = np.asarray(wrapped, dtype=float)
    n, n_p, _ = wrapped.shape
    circ = []
    dtw = []
    for c in range(n_p):
        circ.append(pairwise_circular_matrix(wrapped[:, c, :]))
        U = np.stack([crp_similarity_profile(wrapped[i, c, :]) for i in range(n)], axis=0)
        dtw.append(pairwise_dtw_matrix(U))
    # keys match permute_shape_stats / bootstrap (pearson slot = circular)
    return {"pearson": circ, "dtw": dtw}


def build_subject_crp_profiles(
    cube: np.ndarray,
    inventory: pd.DataFrame,
    signals: list[str],
    pairs: list[dict],
) -> dict:
    """Subject circular-mean CRP: (n_subjects, n_pairs, 101) wrapped radians."""
    sig_to_i = {s: i for i, s in enumerate(signals)}
    ax = AXIS_TO_IDX["ax1"]
    for p in pairs:
        if p["proximal"] not in sig_to_i or p["distal"] not in sig_to_i:
            raise RuntimeError(f"pair {p['id']} missing from Phase 1 core")
    subjects = np.array(sorted(inventory["subject_id"].astype(str).unique()))
    sid_to_i = {s: i for i, s in enumerate(subjects)}
    n_s, n_p = len(subjects), len(pairs)
    buckets: list[list[list[np.ndarray]]] = [[[] for _ in range(n_p)] for _ in range(n_s)]
    inv = inventory.reset_index(drop=True)
    for row_i, row in inv.iterrows():
        sid = str(row["subject_id"])
        if sid not in sid_to_i:
            continue
        si = sid_to_i[sid]
        for pi, pair in enumerate(pairs):
            prox = cube[row_i, sig_to_i[pair["proximal"]], :, ax]
            dist = cube[row_i, sig_to_i[pair["distal"]], :, ax]
            buckets[si][pi].append(continuous_relative_phase(prox, dist))

    wrapped = np.full((n_s, n_p, N_PHASE), np.nan, dtype=float)
    n_cycles = np.zeros(n_s, dtype=int)
    for si in range(n_s):
        n_cycles[si] = min((len(buckets[si][pi]) for pi in range(n_p)), default=0)
        for pi in range(n_p):
            if not buckets[si][pi]:
                continue
            wrapped[si, pi, :] = circular_mean_crp(np.vstack(buckets[si][pi]))

    if not np.isfinite(wrapped).all():
        raise RuntimeError("non-finite CRP profiles after subject aggregation")
    return {
        "subject_id": subjects,
        "X": wrapped,
        "wrapped_crp": wrapped,
        "pair_ids": [p["id"] for p in pairs],
        "n_cycles": n_cycles,
        "raw_crp_note": "X = wrapped circular-mean Hilbert CRP (rad)",
    }


@dataclass
class CoordinationResult:
    representation: str
    n_subjects: int
    n_victims: int
    n_controls: int
    n_pairs: int
    crp_method: str
    mean_pairwise_pearson: float
    pearson_ci_low: float
    pearson_ci_high: float
    perm_p_pearson: float
    null_mean_pearson: float
    mean_pairwise_dtw: float
    dtw_ci_low: float
    dtw_ci_high: float
    perm_p_dtw: float
    null_mean_dtw: float
    n_perm: int
    loso_pass: bool
    loso_sign_agreement: float
    n_pairs_pearson_fdr_le_0_10: int
    n_pairs_dtw_fdr_le_0_10: int
    n_fdr_family: int
    residualized: bool
    residual_covariates: tuple[str, ...]
    seed: int

    def to_dict(self) -> dict:
        return asdict(self)


def per_pair_fdr_table(perm: dict, pair_ids: list[str]) -> pd.DataFrame:
    n_perm = perm["n_perm"]
    rows = []
    raw_p = []
    for j, pid in enumerate(pair_ids):
        obs_p = float(perm["pearson_per_curve"][j])
        obs_d = float(perm["dtw_per_curve"][j])
        null_p = perm["null_pearson_per_curve"][:, j]
        null_d = perm["null_dtw_per_curve"][:, j]
        pp = (1 + int(np.sum(null_p >= obs_p - 1e-15))) / (n_perm + 1)
        pd_ = (1 + int(np.sum(null_d <= obs_d + 1e-15))) / (n_perm + 1)
        rows.append(
            {
                "pair": pid,
                "measure": "circular",
                "observed": obs_p,
                "null_mean": float(np.mean(null_p)),
                "raw_p": float(pp),
            }
        )
        raw_p.append(pp)
        rows.append(
            {
                "pair": pid,
                "measure": "dtw",
                "observed": obs_d,
                "null_mean": float(np.mean(null_d)),
                "raw_p": float(pd_),
            }
        )
        raw_p.append(pd_)
    out = pd.DataFrame(rows)
    out["fdr_q"] = benjamini_hochberg(np.asarray(raw_p, dtype=float))
    return out.sort_values("raw_p").reset_index(drop=True)


def run_coordination_crp(
    wrapped_crp: np.ndarray,
    victim: np.ndarray,
    pair_ids: list[str],
    *,
    representation: str = "hilbert_crp_circular",
    n_perm: int = N_PERM_DEFAULT,
    n_boot: int = N_BOOT_DEFAULT,
    seed: int = SEED,
    residualized: bool = False,
    residual_covariates: tuple[str, ...] = (),
    show_progress: bool = False,
) -> tuple[CoordinationResult, dict]:
    """wrapped_crp: (n_subjects, n_pairs, 101) circular-mean Hilbert CRP (rad)."""
    if wrapped_crp.shape[1] != len(pair_ids):
        raise ValueError("pair_ids length mismatch")
    if wrapped_crp.shape[2] != N_PHASE:
        raise ValueError(f"expected {N_PHASE} phase points")
    victim = np.asarray(victim, dtype=bool)
    if show_progress:
        print(f"  building CRP pairwise banks ({wrapped_crp.shape[1]} pairs) ...")
    banks = build_crp_banks(wrapped_crp)
    if show_progress:
        print(f"  permuting ({n_perm}) ...")
    perm = permute_shape_stats(banks, victim, n_perm=n_perm, seed=seed)
    boot = bootstrap_mean_pairwise(banks, victim, n_boot=n_boot, seed=seed)
    loso = loso_shape_stats(banks, victim)
    pair_tab = per_pair_fdr_table(perm, pair_ids)
    n_fdr_p = int(((pair_tab["measure"] == "circular") & (pair_tab["fdr_q"] <= 0.10)).sum())
    n_fdr_d = int(((pair_tab["measure"] == "dtw") & (pair_tab["fdr_q"] <= 0.10)).sum())

    summary = CoordinationResult(
        representation=representation,
        n_subjects=int(wrapped_crp.shape[0]),
        n_victims=int(victim.sum()),
        n_controls=int((~victim).sum()),
        n_pairs=int(wrapped_crp.shape[1]),
        crp_method="hilbert_analytic_phase",
        mean_pairwise_pearson=perm["observed_pearson"],  # circular similarity
        pearson_ci_low=boot["pearson_ci_low"],
        pearson_ci_high=boot["pearson_ci_high"],
        perm_p_pearson=perm["perm_p_pearson"],
        null_mean_pearson=perm["null_mean_pearson"],
        mean_pairwise_dtw=perm["observed_dtw"],
        dtw_ci_low=boot["dtw_ci_low"],
        dtw_ci_high=boot["dtw_ci_high"],
        perm_p_dtw=perm["perm_p_dtw"],
        null_mean_dtw=perm["null_mean_dtw"],
        n_perm=perm["n_perm"],
        loso_pass=loso["loso_pass"],
        loso_sign_agreement=loso["loso_sign_agreement"],
        n_pairs_pearson_fdr_le_0_10=n_fdr_p,
        n_pairs_dtw_fdr_le_0_10=n_fdr_d,
        n_fdr_family=int(len(pair_tab)),
        residualized=residualized,
        residual_covariates=residual_covariates,
        seed=seed,
    )
    details = {
        "wrapped_crp": wrapped_crp,
        "banks": banks,
        "perm": perm,
        "bootstrap": boot,
        "loso": loso,
        "pair_table": pair_tab,
    }
    return summary, details