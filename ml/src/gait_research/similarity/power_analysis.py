"""P0.1 power / minimum-detectable-effect (MDE) via simulation.

Does not modify Phases 0–6 or frozen P0.1–P0.6 results. Headline MDE uses
signal injection on the frozen residualized 31-point Phase 4 cloud (so λ=0
is the P0.1 permutation experiment). The MVN path reuses the shared-direction
generator from tests/similarity/test_deviation.py::test_shared_direction_detected
and is kept for unit tests.

Effect size λ
-------------
Shared-direction Euclidean magnitude as a fraction of the typical individual
control deviation-vector norm:

    offset = λ * median_i ||d_i^{control}|| * u

where u is a unit vector (random on the sphere, matching the unit-test
generator). λ = 0 is pure noise (calibration); λ ≫ 1 is an obvious shared
offset relative to how far controls already sit from their own centroid.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from sklearn.covariance import LedoitWolf

from .deviation import (
    SEED,
    control_referenced_deviations,
    mean_pairwise_cosine,
    permute_mean_pairwise_cosine,
)

try:
    from numba import njit
except ImportError:  # pragma: no cover
    njit = None

N_V = 17
N_C = 14
N_SIM_DEFAULT = 1000
N_PERM_POWER = 999  # documented reduction vs P0.1's 9999; see mde_report.md
ALPHA = 0.05
POWER_TARGET = 0.80
# Principled sweep: 0 (calibration) through several × typical individual
# deviation, plus a large value that must approach 100% detection.
LAMBDA_GRID_DEFAULT = (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0)


def simulate_shared_direction_dataset(
    n_v: int,
    n_c: int,
    d: int,
    *,
    direction: np.ndarray | None = None,
    scales: np.ndarray | None = None,
    noise_scale: float = 0.3,
    rng: np.random.Generator | None = None,
    Sigma: np.ndarray | None = None,
    mu: np.ndarray | None = None,
    offset_norm: float | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Shared-direction synthetic data (unit-test generator + optional MVN noise).

    Default path matches test_deviation.test_shared_direction_detected:
    isotropic Gaussian noise plus a shared unit direction times positive scales.

    If Sigma is provided, noise is MVN(0, Sigma) and the shared offset has
    Euclidean length ``offset_norm`` along ``direction`` (unit).
    """
    rng = np.random.default_rng() if rng is None else rng
    if direction is None:
        direction = rng.normal(size=d)
    direction = np.asarray(direction, dtype=float).ravel()
    nrm = np.linalg.norm(direction)
    if nrm <= 0:
        raise ValueError("direction must have positive norm")
    direction = direction / nrm

    if Sigma is None:
        controls = rng.normal(scale=noise_scale, size=(n_c, d))
        if scales is None:
            scales = rng.uniform(0.8, 2.5, size=n_v)
        scales = np.asarray(scales, dtype=float).ravel()
        victims = rng.normal(scale=noise_scale, size=(n_v, d)) + scales[:, None] * direction
        if mu is not None:
            victims = victims + np.asarray(mu, dtype=float)
            controls = controls + np.asarray(mu, dtype=float)
    else:
        Sigma = np.asarray(Sigma, dtype=float)
        mu = np.zeros(d) if mu is None else np.asarray(mu, dtype=float).ravel()
        if offset_norm is None:
            raise ValueError("offset_norm required when Sigma is set")
        noise_v = rng.multivariate_normal(np.zeros(d), Sigma, size=n_v)
        noise_c = rng.multivariate_normal(np.zeros(d), Sigma, size=n_c)
        victims = mu + offset_norm * direction + noise_v
        controls = mu + noise_c

    X = np.vstack([victims, controls])
    y = np.zeros(n_v + n_c, dtype=bool)
    y[:n_v] = True
    return X, y, direction


def fit_control_noise_model(X: np.ndarray, victim: np.ndarray) -> dict:
    """Covariance of control-referenced residualized deviations.

    P0.1 permutes all 31 subject points in this space. Fitting Ledoit–Wolf on
    the 14 controls alone (n < d) shrinks ~45% toward identity and produces a
    λ=0 cosine distribution that is too concentrated near 0 relative to the
    frozen residualized permutation null. The noise model is therefore
    Ledoit–Wolf on all 31 control-referenced deviation vectors — the same
    cloud the permutation test actually shuffles — still referenced to the
    control centroid.
    """
    X = np.asarray(X, dtype=float)
    victim = np.asarray(victim, dtype=bool)
    D, mu_c = control_referenced_deviations(X, victim)
    D_c = D[~victim]
    if D_c.shape[0] < 2:
        raise ValueError("need ≥2 controls for a noise model")
    lw_ctrl = LedoitWolf().fit(D_c)
    lw = LedoitWolf().fit(D)
    Sigma = np.asarray(lw.covariance_, dtype=float)
    norms_c = np.linalg.norm(D_c, axis=1)
    typical_norm = float(np.median(norms_c))
    if typical_norm <= 0:
        raise RuntimeError("median control deviation norm is 0")
    return {
        "Sigma": Sigma,
        "mu": mu_c,
        "typical_norm": typical_norm,
        "control_norms": norms_c,
        "mean_control_norm": float(np.mean(norms_c)),
        "n_controls": int(D_c.shape[0]),
        "n_dims": int(D.shape[1]),
        "ledoit_wolf_shrinkage": float(lw.shrinkage_),
        "ledoit_wolf_shrinkage_controls_only": float(lw_ctrl.shrinkage_),
        "source": "ledoit_wolf_all_31_control_referenced_deviations",
        "note": (
            "controls-only LW failed the frozen-null shape check "
            f"(shrinkage={float(lw_ctrl.shrinkage_):.3f}); using all 31 D_i"
        ),
    }


if njit is not None:

    @njit(cache=True)
    def _mean_pairwise_cosine_numba(D: np.ndarray) -> float:
        n = D.shape[0]
        d = D.shape[1]
        if n < 2:
            return np.nan
        norms = np.empty(n)
        for i in range(n):
            s = 0.0
            for k in range(d):
                s += D[i, k] * D[i, k]
            norms[i] = np.sqrt(s)
        acc = 0.0
        n_ok = 0
        for i in range(n):
            if norms[i] <= 0.0:
                continue
            for j in range(i + 1, n):
                if norms[j] <= 0.0:
                    continue
                dot = 0.0
                for k in range(d):
                    dot += D[i, k] * D[j, k]
                acc += dot / (norms[i] * norms[j])
                n_ok += 1
        if n_ok == 0:
            return np.nan
        return acc / n_ok

    @njit(cache=True)
    def _stat_labeled(X: np.ndarray, mask: np.ndarray) -> float:
        n, d = X.shape
        n_c = 0
        n_v = 0
        for i in range(n):
            if mask[i]:
                n_v += 1
            else:
                n_c += 1
        if n_v < 2 or n_c < 1:
            return np.nan
        mu = np.zeros(d)
        for i in range(n):
            if not mask[i]:
                for k in range(d):
                    mu[k] += X[i, k]
        inv_c = 1.0 / n_c
        for k in range(d):
            mu[k] *= inv_c
        D = np.empty((n_v, d))
        t = 0
        for i in range(n):
            if mask[i]:
                for k in range(d):
                    D[t, k] = X[i, k] - mu[k]
                t += 1
        return _mean_pairwise_cosine_numba(D)

    @njit(cache=True)
    def _perm_from_picks(X: np.ndarray, victim: np.ndarray, picks: np.ndarray) -> tuple:
        """picks: (n_perm, n_v) subject indices drawn with the P0.1 Generator."""
        n = X.shape[0]
        n_perm = picks.shape[0]
        n_v = picks.shape[1]
        obs = _stat_labeled(X, victim)
        ge = 0
        mask = np.zeros(n, dtype=np.bool_)
        for p in range(n_perm):
            for i in range(n):
                mask[i] = False
            for j in range(n_v):
                mask[picks[p, j]] = True
            val = _stat_labeled(X, mask)
            if val >= obs - 1e-15:
                ge += 1
        pval = (1.0 + ge) / (n_perm + 1.0)
        return obs, pval

else:  # pragma: no cover

    def _perm_from_picks(X: np.ndarray, victim: np.ndarray, picks: np.ndarray) -> tuple:
        D, _ = control_referenced_deviations(X, victim)
        obs = mean_pairwise_cosine(D[victim])
        ge = 0
        n_perm = int(picks.shape[0])
        for p in range(n_perm):
            mask = np.zeros(X.shape[0], dtype=bool)
            mask[picks[p]] = True
            Dp, _ = control_referenced_deviations(X, mask)
            if mean_pairwise_cosine(Dp[mask]) >= obs - 1e-15:
                ge += 1
        return float(obs), float((1 + ge) / (n_perm + 1))


def permutation_p_cosine(X: np.ndarray, victim: np.ndarray, *, n_perm: int, seed: int) -> tuple[float, float]:
    """Same one-sided permutation p as P0.1 (same Generator draws + same statistic)."""
    X = np.asarray(X, dtype=np.float64)
    victim = np.asarray(victim, dtype=np.bool_)
    n = X.shape[0]
    n_v = int(victim.sum())
    rng = np.random.default_rng(seed)
    idx = np.arange(n)
    picks = np.empty((int(n_perm), n_v), dtype=np.int64)
    for i in range(int(n_perm)):
        picks[i] = rng.choice(idx, size=n_v, replace=False)
    obs, p = _perm_from_picks(X, victim, picks)
    return float(obs), float(p)


def simulate_empirical_injection(
    X_empirical: np.ndarray,
    *,
    lam: float,
    typical_norm: float,
    n_v: int = N_V,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Signal injection on the frozen residualized 31-point cloud.

    Randomly partitions the empirical points into 17/14, then adds a shared
    offset of length ``lam * typical_norm`` to the 17. At λ=0 this *is* the
    P0.1 permutation experiment, so the λ=0 cosine distribution matches the
    frozen residualized null by construction.
    """
    X_empirical = np.asarray(X_empirical, dtype=float)
    n, d = X_empirical.shape
    if n_v >= n:
        raise ValueError("n_v must be < n")
    idx = rng.permutation(n)
    X = X_empirical[idx].copy()
    y = np.zeros(n, dtype=bool)
    y[:n_v] = True
    if lam > 0:
        direction = rng.normal(size=d)
        direction /= np.linalg.norm(direction)
        X[:n_v] += float(lam) * float(typical_norm) * direction
    return X, y


def interpolate_mde(lambdas, power, *, target: float = POWER_TARGET) -> float:
    """Smallest λ where power reaches ``target``, linear interpolation on the grid."""
    lambdas = np.asarray(lambdas, dtype=float)
    power = np.asarray(power, dtype=float)
    order = np.argsort(lambdas)
    lambdas = lambdas[order]
    power = power[order]
    if power[-1] < target:
        return float("nan")
    if power[0] >= target:
        return float(lambdas[0])
    for i in range(1, lambdas.size):
        if power[i] >= target:
            p0, p1 = power[i - 1], power[i]
            l0, l1 = lambdas[i - 1], lambdas[i]
            if p1 <= p0:
                return float(l1)
            w = (target - p0) / (p1 - p0)
            return float(l0 + w * (l1 - l0))
    return float("nan")


def compare_null_moments(sim_null: np.ndarray, real_null: np.ndarray) -> dict:
    """Shape check: simulated vs frozen P0.1 permutation null (mean/sd)."""
    sim = np.asarray(sim_null, dtype=float)
    real = np.asarray(real_null, dtype=float)
    sim = sim[np.isfinite(sim)]
    real = real[np.isfinite(real)]
    sm, ss = float(np.mean(sim)), float(np.std(sim, ddof=1))
    rm, rs = float(np.mean(real)), float(np.std(real, ddof=1))
    return {
        "sim_mean": sm,
        "sim_sd": ss,
        "real_mean": rm,
        "real_sd": rs,
        "rel_mean_diff": abs(sm - rm) / (abs(rm) + 1e-12),
        "rel_sd_diff": abs(ss - rs) / (abs(rs) + 1e-12),
    }


@dataclass
class PowerCurveResult:
    lambdas: tuple[float, ...]
    n_sim: int
    n_perm: int
    alpha: float
    power: tuple[float, ...]
    mean_observed_cosine: tuple[float, ...]
    n_reject: tuple[int, ...]
    mde_lambda_80: float
    mde_mean_cosine_80: float
    fpr_at_zero: float
    power_at_large: float
    typical_norm: float
    ledoit_wolf_shrinkage: float
    observed_p01_cosine: float
    seed: int

    def to_dict(self) -> dict:
        return asdict(self)


def run_power_curve(
    Sigma: np.ndarray | None,
    mu: np.ndarray | None,
    typical_norm: float,
    *,
    lambdas: tuple[float, ...] = LAMBDA_GRID_DEFAULT,
    n_sim: int = N_SIM_DEFAULT,
    n_perm: int = N_PERM_POWER,
    n_v: int = N_V,
    n_c: int = N_C,
    alpha: float = ALPHA,
    seed: int = SEED,
    observed_p01_cosine: float = 0.0518,
    progress: bool = False,
    X_empirical: np.ndarray | None = None,
) -> tuple[PowerCurveResult, dict]:
    """Sweep λ; each replicate runs the P0.1 permutation cosine test.

    If ``X_empirical`` is set, datasets are signal-injected partitions of that
    frozen cloud (primary P0.1 MDE). Otherwise MVN(mu, Sigma) is used
    (unit-test / calibration path).
    """
    if X_empirical is None:
        if Sigma is None or mu is None:
            raise ValueError("Sigma and mu required when X_empirical is None")
        Sigma = np.asarray(Sigma, dtype=float)
        mu = np.asarray(mu, dtype=float).ravel()
        d = Sigma.shape[0]
    rng = np.random.default_rng(seed)
    powers = []
    mean_cos = []
    n_rej = []
    obs_at_zero: list[float] = []
    iterator = lambdas
    if progress:
        from tqdm import tqdm

        iterator = tqdm(lambdas, desc="P0.1 power lambda sweep")

    for lam in iterator:
        offset = float(lam) * typical_norm
        rejects = 0
        cos_acc = []
        for s in range(n_sim):
            if X_empirical is not None:
                X, y = simulate_empirical_injection(
                    X_empirical, lam=float(lam), typical_norm=typical_norm, n_v=n_v, rng=rng
                )
            else:
                X, y, _ = simulate_shared_direction_dataset(
                    n_v,
                    n_c,
                    d,
                    rng=rng,
                    Sigma=Sigma,
                    mu=mu,
                    offset_norm=offset,
                )
            obs, p = permutation_p_cosine(X, y, n_perm=n_perm, seed=int(rng.integers(0, 2**31 - 1)))
            cos_acc.append(obs)
            if p <= alpha:
                rejects += 1
            if abs(lam) < 1e-15:
                obs_at_zero.append(obs)
        pw = rejects / n_sim
        powers.append(pw)
        mean_cos.append(float(np.mean(cos_acc)))
        n_rej.append(int(rejects))

    lam_a = np.asarray(lambdas, dtype=float)
    pow_a = np.asarray(powers, dtype=float)
    cos_a = np.asarray(mean_cos, dtype=float)
    mde = interpolate_mde(lam_a, pow_a, target=POWER_TARGET)
    if np.isfinite(mde):
        mde_cos = float(np.interp(mde, lam_a, cos_a))
    else:
        mde_cos = float("nan")

    summary = PowerCurveResult(
        lambdas=tuple(float(x) for x in lambdas),
        n_sim=n_sim,
        n_perm=n_perm,
        alpha=alpha,
        power=tuple(float(x) for x in powers),
        mean_observed_cosine=tuple(float(x) for x in mean_cos),
        n_reject=tuple(int(x) for x in n_rej),
        mde_lambda_80=float(mde),
        mde_mean_cosine_80=mde_cos,
        fpr_at_zero=float(powers[0]) if abs(lambdas[0]) < 1e-15 else float("nan"),
        power_at_large=float(powers[-1]),
        typical_norm=float(typical_norm),
        ledoit_wolf_shrinkage=float("nan"),
        observed_p01_cosine=float(observed_p01_cosine),
        seed=seed,
    )
    details = {"obs_cosine_at_lambda0": np.asarray(obs_at_zero, dtype=float)}
    return summary, details
