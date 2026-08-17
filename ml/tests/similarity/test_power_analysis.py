"""Synthetic + calibration tests for P0.1 power / MDE analysis."""

from __future__ import annotations

import numpy as np
import pytest

from gait_research.similarity.deviation import (
    control_referenced_deviations,
    mean_pairwise_cosine,
    permute_mean_pairwise_cosine,
)
from gait_research.similarity.power_analysis import (
    compare_null_moments,
    interpolate_mde,
    permutation_p_cosine,
    run_power_curve,
    simulate_empirical_injection,
    simulate_shared_direction_dataset,
)


def test_generator_shared_direction_still_detects():
    """Reuse of the P0.1 unit-test generator: shared direction must reject."""
    rng = np.random.default_rng(0)
    X, y, _ = simulate_shared_direction_dataset(17, 14, 27, rng=rng)
    obs, p = permutation_p_cosine(X, y, n_perm=199, seed=1)
    assert obs > 0.5
    assert p < 0.05


def test_fast_perm_matches_p01_implementation():
    rng = np.random.default_rng(7)
    X = rng.normal(size=(31, 12))
    y = np.zeros(31, dtype=bool)
    y[:17] = True
    ref = permute_mean_pairwise_cosine(X, y, n_perm=80, seed=11)
    obs, p = permutation_p_cosine(X, y, n_perm=80, seed=11)
    assert obs == pytest.approx(ref["observed"], abs=1e-9)
    assert p == pytest.approx(ref["perm_p"], abs=1e-12)


def test_interpolate_mde():
    lam = np.array([0.0, 1.0, 2.0])
    pw = np.array([0.05, 0.50, 0.90])
    mde = interpolate_mde(lam, pw, target=0.80)
    assert mde == pytest.approx(1.0 + 0.3 / 0.4, abs=1e-9)
    assert np.isnan(interpolate_mde(lam, np.array([0.05, 0.1, 0.2]), target=0.80))


def test_false_positive_rate_near_alpha_at_zero():
    """λ=0 must be calibrated (~5% rejections)."""
    d = 10
    Sigma = np.eye(d) * 0.09
    summary, _ = run_power_curve(
        Sigma,
        np.zeros(d),
        typical_norm=1.0,
        lambdas=(0.0,),
        n_sim=250,
        n_perm=99,
        seed=3,
        progress=False,
    )
    assert 0.01 <= summary.fpr_at_zero <= 0.12


def test_large_effect_power_approaches_one():
    d = 10
    Sigma = np.eye(d) * 0.09
    summary, _ = run_power_curve(
        Sigma,
        np.zeros(d),
        typical_norm=1.0,
        lambdas=(3.0,),
        n_sim=40,
        n_perm=79,
        seed=4,
        progress=False,
    )
    assert summary.power_at_large >= 0.90


def test_empirical_lambda0_matches_perm_null():
    """λ=0 injection on a fixed cloud must reproduce that cloud's permutation null."""
    rng = np.random.default_rng(8)
    X = rng.normal(size=(31, 8))
    y = np.zeros(31, dtype=bool)
    y[:17] = True
    real = permute_mean_pairwise_cosine(X, y, n_perm=400, seed=8)["null"]
    sims = []
    for _ in range(400):
        Xs, ys = simulate_empirical_injection(X, lam=0.0, typical_norm=1.0, rng=rng)
        D, _ = control_referenced_deviations(Xs, ys)
        sims.append(mean_pairwise_cosine(D[ys]))
    cmp_ = compare_null_moments(np.asarray(sims), real)
    assert cmp_["rel_mean_diff"] < 0.25
    assert cmp_["rel_sd_diff"] < 0.35
