"""Synthetic + analytic tests for P0.6 Hilbert CRP coordination."""

from __future__ import annotations

import numpy as np
import pytest

from gait_research.similarity.coordination_crp import (
    circular_curve_sim,
    continuous_relative_phase,
    crp_similarity_profile,
    hilbert_phase,
    run_coordination_crp,
    wrap_pi,
)
from gait_research.similarity.shape_space import residualize_curves


def _labels(n_v=17, n_c=14):
    y = np.zeros(n_v + n_c, dtype=bool)
    y[:n_v] = True
    return y


def _ids(n: int) -> list[str]:
    return [f"pair{j}" for j in range(n)]


def test_hilbert_crp_constant_for_phase_offset_sinusoids():
    """Two sinusoids with fixed lag → nearly constant CRP ≈ lag."""
    t = np.linspace(0, 2 * np.pi, 101, endpoint=False)
    lag = np.pi / 3
    a = np.sin(t)
    b = np.sin(t - lag)
    crp = continuous_relative_phase(a, b)
    assert np.std(wrap_pi(crp - np.mean(crp))) < 0.15
    assert abs(wrap_pi(np.mean(crp) - lag)) < 0.2 or abs(wrap_pi(np.mean(crp) + lag)) < 0.2


def test_circular_sim_identical_constant():
    a = np.full(101, 0.7)
    assert circular_curve_sim(a, a) == pytest.approx(1.0)
    assert circular_curve_sim(a, a + 0.1) > circular_curve_sim(a, a + 2.0)


def test_shared_coupling_independent_marginals_detected():
    """Victims share phase offset; amplitudes differ → P0.1–P0.4-blind case."""
    rng = np.random.default_rng(0)
    n_v, n_c, n_pairs, n_t = 17, 14, 4, 101
    t = np.linspace(0, 2 * np.pi, n_t, endpoint=False)
    shared_lag = 0.7
    wrapped = np.zeros((n_v + n_c, n_pairs, n_t))
    for j in range(n_pairs):
        for i in range(n_v):
            a1, a2 = rng.uniform(0.5, 3.0, size=2)
            prox = a1 * np.sin(t) + rng.normal(scale=0.02, size=n_t)
            dist = a2 * np.sin(t - shared_lag) + rng.normal(scale=0.02, size=n_t)
            wrapped[i, j] = continuous_relative_phase(prox, dist)
        for i in range(n_v, n_v + n_c):
            lag = rng.uniform(-2.5, 2.5)
            a1, a2 = rng.uniform(0.5, 3.0, size=2)
            prox = a1 * np.sin(t) + rng.normal(scale=0.02, size=n_t)
            dist = a2 * np.sin(t - lag) + rng.normal(scale=0.02, size=n_t)
            wrapped[i, j] = continuous_relative_phase(prox, dist)
    y = _labels(n_v, n_c)
    summary, _ = run_coordination_crp(wrapped, y, _ids(n_pairs), n_perm=299, n_boot=100, seed=1)
    assert summary.mean_pairwise_pearson > 0.5  # circular slot
    assert summary.perm_p_pearson < 0.05


def test_independent_coupling_not_detected():
    rng = np.random.default_rng(1)
    n_t = 101
    t = np.linspace(0, 2 * np.pi, n_t, endpoint=False)
    wrapped = np.zeros((31, 4, n_t))
    for j in range(4):
        for i in range(31):
            lag = rng.uniform(-2.5, 2.5)
            prox = rng.uniform(0.5, 2.0) * np.sin(t)
            dist = rng.uniform(0.5, 2.0) * np.sin(t - lag)
            wrapped[i, j] = continuous_relative_phase(prox, dist)
    y = _labels()
    summary, _ = run_coordination_crp(wrapped, y, _ids(4), n_perm=299, n_boot=100, seed=2)
    assert summary.perm_p_pearson > 0.05
    assert summary.perm_p_dtw > 0.05


def test_one_outlier_moves_loso():
    n_v, n_c, n_pairs, n_t = 17, 14, 3, 101
    t = np.linspace(0, 2 * np.pi, n_t, endpoint=False)
    wrapped = np.zeros((n_v + n_c, n_pairs, n_t))
    for j in range(n_pairs):
        for i in range(1, n_v):
            wrapped[i, j] = continuous_relative_phase(np.sin(t), np.sin(t - 0.8))
        wrapped[0, j] = continuous_relative_phase(np.sin(t), np.sin(t + 2.0))
        for i in range(n_v, n_v + n_c):
            wrapped[i, j] = continuous_relative_phase(np.sin(t), np.sin(t - 0.1 * (i - n_v)))
    y = _labels(n_v, n_c)
    from gait_research.similarity.coordination_crp import build_crp_banks
    from gait_research.similarity.shape_space import loso_shape_stats

    banks = build_crp_banks(wrapped)
    loso = loso_shape_stats(banks, y)
    assert loso["loso_pearson"][0] > loso["full_pearson"] + 0.02


def test_hilbert_phase_length():
    x = np.sin(np.linspace(0, 2 * np.pi, 101, endpoint=False))
    ph = hilbert_phase(x)
    assert ph.shape == (101,)
    assert np.isfinite(ph).all()


def test_residualize_preserves_shape():
    rng = np.random.default_rng(4)
    X = rng.normal(size=(31, 3, 101))
    h = np.linspace(150, 180, 31)
    Xr = residualize_curves(X, h)
    assert Xr.shape == X.shape
