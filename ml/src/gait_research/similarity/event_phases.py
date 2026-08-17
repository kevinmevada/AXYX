"""P0.4 — Event-localized phase-window similarity.

Question
--------
Is victim similarity localized to specific clinical gait phases that whole-cycle
tests (P0.1–P0.3) dilute?

Phases
------
Only windows reconstructable from Phase 1 stored events (IC, opposite FO,
mid-stance, opposite FC, ipsilateral FO, next IC). ISw/MSw/TSw are NOT
estimated. Locked in preregistered_phases.json before any real test.

Per cell
--------
phase × P0.3 curve × {mean, rom} × {deviation_cosine, abnormality_jaccard}.
FDR spans the entire pre-registered family (not per-window).

Statistics reuse deviation.py / abnormality.py — this module is windowing +
orchestration only.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from tqdm import tqdm

from ..features.base import N_PHASE
from ..statistics.multiple_testing import benjamini_hochberg
from .abnormality import (
    BAND_HI,
    BAND_LO,
    build_exceedance,
    loso_mean_pairwise_jaccard,
    mean_pairwise_jaccard,
    permute_mean_pairwise_jaccard,
)
from .deviation import (
    control_referenced_deviations,
    loso_mean_pairwise_cosine,
    mean_pairwise_cosine,
    permute_mean_pairwise_cosine,
    residualize_columns,
)
from .shape_space import AXIS_TO_IDX, load_preregistered_curves

SEED = 20260813
N_PERM_DEFAULT = 9999
N_BOOT_DEFAULT = 2000


def load_preregistered_phases(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    phases = list(payload["phases"])
    if len(phases) != int(payload["n_phases"]):
        raise RuntimeError("n_phases mismatch")
    expected = int(payload["n_fdr_family"])
    got = (
        int(payload["n_phases"])
        * int(payload["n_curves"])
        * int(payload["n_aggregations"])
        * int(payload["n_test_types"])
    )
    if expected != got:
        raise RuntimeError(f"n_fdr_family {expected} != product {got}")
    return payload


def frame_to_pct(frame: float, start: float, end: float) -> float:
    dur = float(end) - float(start)
    if dur <= 0:
        return float("nan")
    return 100.0 * (float(frame) - float(start)) / dur


def pct_to_index(pct: float, n: int = N_PHASE) -> int:
    if not np.isfinite(pct):
        return 0
    return int(np.clip(round(pct * (n - 1) / 100.0), 0, n - 1))


def cycle_phase_bounds_pct(row: pd.Series) -> dict[str, tuple[float, float]]:
    """Event-derived phase windows in % gait cycle for one inventory row."""
    start = float(row["initial_contact_frame"])
    end = float(row["next_contact_frame"])
    opp_fo = frame_to_pct(row["opposite_foot_off_frame"], start, end)
    ms = frame_to_pct(row["mid_stance_frame"], start, end)
    opp_fc = frame_to_pct(row["opposite_contact_frame"], start, end)
    ipsi_fo = frame_to_pct(row["ipsilateral_foot_off_frame"], start, end)
    bounds = {
        "loading_response": (0.0, opp_fo),
        "mid_stance": (opp_fo, ms),
        "terminal_stance": (ms, opp_fc),
        "pre_swing": (opp_fc, ipsi_fo),
        "swing": (ipsi_fo, 100.0),
    }
    for name, (lo, hi) in bounds.items():
        if not (np.isfinite(lo) and np.isfinite(hi) and hi > lo):
            raise ValueError(f"invalid bounds for {name}: {(lo, hi)}")
    return bounds


def window_agg(series: np.ndarray, lo_pct: float, hi_pct: float, how: str) -> float:
    """Aggregate a 101-pt curve over [lo_pct, hi_pct]. hi is exclusive except at 100%."""
    series = np.asarray(series, dtype=float).ravel()
    i0 = pct_to_index(lo_pct)
    i1 = pct_to_index(hi_pct)
    if hi_pct >= 100.0 - 1e-9:
        sl = series[i0 : i1 + 1]
    else:
        # exclusive end index; ensure at least 1 sample
        if i1 <= i0:
            i1 = min(i0 + 1, series.size)
        sl = series[i0:i1]
    if sl.size == 0 or not np.isfinite(sl).any():
        return float("nan")
    sl = sl[np.isfinite(sl)]
    if how == "mean":
        return float(np.mean(sl))
    if how == "rom":
        return float(np.max(sl) - np.min(sl))
    raise ValueError(how)


def feature_name(phase_id: str, curve_id: str, agg: str) -> str:
    return f"{phase_id}__{curve_id}__{agg}"


def extract_cycle_window_features(
    curve_block: np.ndarray,
    bounds: dict[str, tuple[float, float]],
    curve_ids: list[str],
    aggregations: list[str],
    phase_ids: list[str],
) -> dict[str, float]:
    """curve_block: (n_curves, 101) for one cycle."""
    out: dict[str, float] = {}
    for phase in phase_ids:
        lo, hi = bounds[phase]
        for c_i, cid in enumerate(curve_ids):
            for agg in aggregations:
                out[feature_name(phase, cid, agg)] = window_agg(curve_block[c_i], lo, hi, agg)
    return out


def build_subject_phase_feature_matrix(
    cube: np.ndarray,
    inventory: pd.DataFrame,
    signals: list[str],
    curves_meta: list[dict],
    phase_ids: list[str],
    aggregations: list[str],
) -> dict:
    """Subject-median of cycle-level window features. Label-blind."""
    sig_to_i = {s: i for i, s in enumerate(signals)}
    curve_ids = [c["id"] for c in curves_meta]
    curve_sig_ax = [(sig_to_i[c["signal"]], AXIS_TO_IDX[c["axis"]]) for c in curves_meta]
    feature_names = [
        feature_name(ph, cid, agg) for ph in phase_ids for cid in curve_ids for agg in aggregations
    ]
    subjects = np.array(sorted(inventory["subject_id"].astype(str).unique()))
    sid_to_i = {s: i for i, s in enumerate(subjects)}
    # accumulate cycles then nanmedian
    buckets: list[list[np.ndarray]] = [[] for _ in subjects]
    inv = inventory.reset_index(drop=True)
    for row_i, row in inv.iterrows():
        sid = str(row["subject_id"])
        if sid not in sid_to_i:
            continue
        bounds = cycle_phase_bounds_pct(row)
        block = np.stack(
            [cube[row_i, si, :, ax] for si, ax in curve_sig_ax],
            axis=0,
        )
        feats = extract_cycle_window_features(block, bounds, curve_ids, aggregations, phase_ids)
        buckets[sid_to_i[sid]].append(np.array([feats[n] for n in feature_names], dtype=float))

    X = np.full((len(subjects), len(feature_names)), np.nan, dtype=float)
    n_cycles = np.zeros(len(subjects), dtype=int)
    for i, parts in enumerate(buckets):
        n_cycles[i] = len(parts)
        if not parts:
            continue
        X[i] = np.nanmedian(np.vstack(parts), axis=0)
    return {
        "subject_id": subjects,
        "X": X,
        "feature_names": feature_names,
        "curve_ids": curve_ids,
        "phase_ids": phase_ids,
        "aggregations": aggregations,
        "n_cycles": n_cycles,
    }


def parse_feature_name(name: str) -> dict[str, str]:
    phase, curve, agg = name.split("__", 2)
    return {"phase": phase, "curve": curve, "aggregation": agg}


def run_cell_deviation(X1: np.ndarray, victim: np.ndarray, *, n_perm: int, seed: int) -> dict:
    """X1: (n_subjects, 1). Reuses deviation permutation."""
    perm = permute_mean_pairwise_cosine(X1, victim, n_perm=n_perm, seed=seed)
    D, _ = control_referenced_deviations(X1, victim)
    return {
        "observed": perm["observed"],
        "null_mean": perm["null_mean"],
        "perm_p": perm["perm_p"],
        "D_victims": D[victim],
    }


def run_cell_abnormality(X1: np.ndarray, victim: np.ndarray, *, n_perm: int, seed: int) -> dict:
    perm = permute_mean_pairwise_jaccard(X1, victim, n_perm=n_perm, seed=seed)
    return {
        "observed": perm["observed"],
        "null_mean": perm["null_mean"],
        "perm_p": perm["perm_p"],
    }


def run_window_multivariate(
    X: np.ndarray,
    feature_names: list[str],
    phase_id: str,
    victim: np.ndarray,
    *,
    n_perm: int,
    seed: int,
) -> dict:
    """All mean/rom features for one phase → P0.1 + P0.2 with LOSO."""
    cols = [i for i, n in enumerate(feature_names) if n.startswith(phase_id + "__")]
    Xp = X[:, cols]
    names = [feature_names[i] for i in cols]
    cos = permute_mean_pairwise_cosine(Xp, victim, n_perm=n_perm, seed=seed)
    jac = permute_mean_pairwise_jaccard(Xp, victim, n_perm=n_perm, seed=seed + 1)
    loso_c = loso_mean_pairwise_cosine(Xp, victim)
    loso_j = loso_mean_pairwise_jaccard(Xp, victim)
    return {
        "phase": phase_id,
        "n_features": len(cols),
        "feature_names": names,
        "deviation_cosine": cos["observed"],
        "deviation_null_mean": cos["null_mean"],
        "deviation_perm_p": cos["perm_p"],
        "deviation_loso_pass": loso_c["loso_pass"],
        "deviation_loso_sign_agreement": loso_c["loso_sign_agreement"],
        "abnormality_jaccard": jac["observed"],
        "abnormality_null_mean": jac["null_mean"],
        "abnormality_perm_p": jac["perm_p"],
        "abnormality_loso_pass": loso_j["loso_pass"],
        "abnormality_loso_top5_agreement": loso_j["top5_feature_rank_agreement"],
    }


@dataclass
class EventPhaseBatteryResult:
    representation: str
    n_subjects: int
    n_victims: int
    n_controls: int
    n_phases: int
    n_curves: int
    n_aggregations: int
    n_fdr_family: int
    n_fdr_le_0_10: int
    n_fdr_le_0_05: int
    min_perm_p: float
    residualized: bool
    residual_covariates: tuple[str, ...]
    n_perm: int
    seed: int

    def to_dict(self) -> dict:
        return asdict(self)


def run_event_phase_battery(
    X: np.ndarray,
    feature_names: list[str],
    victim: np.ndarray,
    phase_ids: list[str],
    *,
    representation: str = "event_phase_windows",
    n_perm: int = N_PERM_DEFAULT,
    seed: int = SEED,
    residualized: bool = False,
    residual_covariates: tuple[str, ...] = (),
    show_progress: bool = False,
    progress_desc: str | None = None,
) -> tuple[EventPhaseBatteryResult, dict]:
    """Run the full pre-registered FDR family + per-window multivariate LOSO."""
    if X.shape[1] != len(feature_names):
        raise ValueError("feature_names length mismatch")
    X = np.asarray(X, dtype=float)
    victim = np.asarray(victim, dtype=bool)
    n, p = X.shape
    n_v = int(victim.sum())
    tag = progress_desc or ("residualized" if residualized else "raw")
    rng = np.random.default_rng(seed)
    # shared subject-label permutations for the whole family
    perm_masks = np.zeros((n_perm, n), dtype=bool)
    idx = np.arange(n)
    for i in tqdm(
        range(n_perm),
        desc=f"P0.4 [{tag}] perm masks",
        leave=False,
        disable=not show_progress,
    ):
        pick = rng.choice(idx, size=n_v, replace=False)
        perm_masks[i, pick] = True

    rows = []
    raw_p = []
    for j, name in tqdm(
        list(enumerate(feature_names)),
        desc=f"P0.4 [{tag}] cells ({len(feature_names)} feats x 2 tests)",
        leave=True,
        disable=not show_progress,
    ):
        meta = parse_feature_name(name)
        x = X[:, j]
        obs_cos, null_cos = _perm_cosine_1d(x, victim, perm_masks)
        ge = int(np.sum(null_cos >= obs_cos - 1e-15)) if np.isfinite(obs_cos) else n_perm
        p_cos = (1 + ge) / (n_perm + 1)
        rows.append(
            {
                "phase": meta["phase"],
                "curve": meta["curve"],
                "aggregation": meta["aggregation"],
                "test_type": "deviation_cosine",
                "feature": name,
                "observed": obs_cos,
                "null_mean": float(np.nanmean(null_cos)),
                "raw_p": float(p_cos),
            }
        )
        raw_p.append(p_cos)

        obs_jac, null_jac = _perm_jaccard_1d(x, victim, perm_masks)
        ge_j = int(np.sum(null_jac >= obs_jac - 1e-15)) if np.isfinite(obs_jac) else n_perm
        p_jac = (1 + ge_j) / (n_perm + 1)
        rows.append(
            {
                "phase": meta["phase"],
                "curve": meta["curve"],
                "aggregation": meta["aggregation"],
                "test_type": "abnormality_jaccard",
                "feature": name,
                "observed": obs_jac,
                "null_mean": float(np.nanmean(null_jac)),
                "raw_p": float(p_jac),
            }
        )
        raw_p.append(p_jac)

    cell_df = pd.DataFrame(rows)
    cell_df["fdr_q"] = benjamini_hochberg(np.asarray(raw_p, dtype=float))
    cell_df = cell_df.sort_values("raw_p").reset_index(drop=True)

    window_rows = []
    for k, ph in tqdm(
        list(enumerate(phase_ids)),
        desc=f"P0.4 [{tag}] window multivariate + LOSO",
        leave=True,
        disable=not show_progress,
    ):
        window_rows.append(
            run_window_multivariate(X, feature_names, ph, victim, n_perm=n_perm, seed=seed + 1000 + k)
        )
    window_df = pd.DataFrame(window_rows)

    summary = EventPhaseBatteryResult(
        representation=representation,
        n_subjects=int(n),
        n_victims=int(n_v),
        n_controls=int((~victim).sum()),
        n_phases=len(phase_ids),
        n_curves=len({parse_feature_name(n_)["curve"] for n_ in feature_names}),
        n_aggregations=len({parse_feature_name(n_)["aggregation"] for n_ in feature_names}),
        n_fdr_family=int(len(cell_df)),
        n_fdr_le_0_10=int((cell_df["fdr_q"] <= 0.10).sum()),
        n_fdr_le_0_05=int((cell_df["fdr_q"] <= 0.05).sum()),
        min_perm_p=float(cell_df["raw_p"].min()),
        residualized=residualized,
        residual_covariates=residual_covariates,
        n_perm=n_perm,
        seed=seed,
    )
    details = {"cell_table": cell_df, "window_table": window_df, "feature_names": feature_names}
    return summary, details


def _mean_pairwise_sign_cosine(d: np.ndarray) -> float:
    """Mean pairwise cosine for 1-D deviations (= mean of sign products for nonzero)."""
    d = np.asarray(d, dtype=float).ravel()
    s = np.sign(d)
    s = s[np.abs(d) > 0]
    n = int(s.size)
    if n < 2:
        return float("nan")
    # mean_{i<j} s_i s_j = ((sum s)^2 - sum s^2) / (n(n-1))
    return float((s.sum() ** 2 - np.dot(s, s)) / (n * (n - 1)))


def _jaccard_1bit_mean(bits: np.ndarray) -> float:
    """Mean pairwise Jaccard for length-1 binary vectors (agree→1, disagree→0)."""
    b = np.asarray(bits, dtype=bool).ravel()
    n = int(b.size)
    if n < 2:
        return float("nan")
    n1 = int(b.sum())
    n0 = n - n1
    return float((n1 * (n1 - 1) + n0 * (n0 - 1)) / (n * (n - 1)))


try:
    from numba import njit

    @njit(cache=True)
    def _perm_cosine_null_numba(x: np.ndarray, perm_masks: np.ndarray) -> np.ndarray:
        n_perm = perm_masks.shape[0]
        n = x.shape[0]
        null = np.empty(n_perm)
        for i in range(n_perm):
            # control mean
            s_ctrl = 0.0
            n_ctrl = 0
            for t in range(n):
                if not perm_masks[i, t]:
                    s_ctrl += x[t]
                    n_ctrl += 1
            mu = s_ctrl / n_ctrl
            # signs of victim deviations
            sum_s = 0.0
            sum_s2 = 0.0
            n_nz = 0
            for t in range(n):
                if perm_masks[i, t]:
                    d = x[t] - mu
                    if d > 0.0:
                        sum_s += 1.0
                        sum_s2 += 1.0
                        n_nz += 1
                    elif d < 0.0:
                        sum_s -= 1.0
                        sum_s2 += 1.0
                        n_nz += 1
            if n_nz < 2:
                null[i] = np.nan
            else:
                null[i] = (sum_s * sum_s - sum_s2) / (n_nz * (n_nz - 1))
        return null

    @njit(cache=True)
    def _perm_jaccard_null_numba(x: np.ndarray, perm_masks: np.ndarray, lo_q: float, hi_q: float) -> np.ndarray:
        n_perm = perm_masks.shape[0]
        n = x.shape[0]
        null = np.empty(n_perm)
        ctrl = np.empty(n)
        for i in range(n_perm):
            n_ctrl = 0
            n_v = 0
            for t in range(n):
                if not perm_masks[i, t]:
                    ctrl[n_ctrl] = x[t]
                    n_ctrl += 1
                else:
                    n_v += 1
            c = ctrl[:n_ctrl].copy()
            c.sort()
            if n_ctrl == 1:
                lo = c[0]
                hi = c[0]
            else:
                pos_lo = (n_ctrl - 1) * lo_q / 100.0
                i0 = int(np.floor(pos_lo))
                i1 = int(np.ceil(pos_lo))
                if i0 == i1:
                    lo = c[i0]
                else:
                    w = pos_lo - i0
                    lo = c[i0] * (1.0 - w) + c[i1] * w
                pos_hi = (n_ctrl - 1) * hi_q / 100.0
                j0 = int(np.floor(pos_hi))
                j1 = int(np.ceil(pos_hi))
                if j0 == j1:
                    hi = c[j0]
                else:
                    w = pos_hi - j0
                    hi = c[j0] * (1.0 - w) + c[j1] * w
            n1 = 0
            for t in range(n):
                if perm_masks[i, t]:
                    if x[t] < lo or x[t] > hi:
                        n1 += 1
            n0 = n_v - n1
            null[i] = (n1 * (n1 - 1) + n0 * (n0 - 1)) / (n_v * (n_v - 1))
        return null

except ImportError:  # pragma: no cover
    _perm_cosine_null_numba = None
    _perm_jaccard_null_numba = None


def _perm_cosine_1d(x: np.ndarray, victim: np.ndarray, perm_masks: np.ndarray) -> tuple[float, np.ndarray]:
    x = np.asarray(x, dtype=np.float64).ravel()
    victim = np.asarray(victim, dtype=bool)
    obs = _mean_pairwise_sign_cosine(x[victim] - float(np.mean(x[~victim])))
    if _perm_cosine_null_numba is not None:
        null = _perm_cosine_null_numba(x, np.asarray(perm_masks, dtype=np.bool_))
    else:
        n_perm = perm_masks.shape[0]
        null = np.empty(n_perm, dtype=float)
        for i in range(n_perm):
            m = perm_masks[i]
            null[i] = _mean_pairwise_sign_cosine(x[m] - float(np.mean(x[~m])))
    return obs, null


def _perm_jaccard_1d(x: np.ndarray, victim: np.ndarray, perm_masks: np.ndarray) -> tuple[float, np.ndarray]:
    """1-D exceedance Jaccard with control 10–90% band recomputed each perm."""
    x = np.asarray(x, dtype=np.float64).ravel()
    victim = np.asarray(victim, dtype=bool)
    lo, hi = np.percentile(x[~victim], [BAND_LO, BAND_HI])
    obs = _jaccard_1bit_mean(((x < lo) | (x > hi))[victim])
    if _perm_jaccard_null_numba is not None:
        null = _perm_jaccard_null_numba(
            x, np.asarray(perm_masks, dtype=np.bool_), float(BAND_LO), float(BAND_HI)
        )
    else:
        n_perm = perm_masks.shape[0]
        null = np.empty(n_perm, dtype=float)
        for i in range(n_perm):
            m = perm_masks[i]
            lo_i, hi_i = np.percentile(x[~m], [BAND_LO, BAND_HI])
            null[i] = _jaccard_1bit_mean(((x < lo_i) | (x > hi_i))[m])
    return obs, null