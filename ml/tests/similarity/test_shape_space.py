"""Synthetic sanity tests for P0.3 shape-space waveform similarity."""

from __future__ import annotations

import numpy as np
import pytest

from gait_research.similarity.shape_space import (
    dtw_distance,
    loso_shape_stats,
    pearson_sim,
    residualize_curves,
    run_shape_space,
    zscore_curves,
)


def _labels(n_v=17, n_c=14):
    y = np.zeros(n_v + n_c, dtype=bool)
    y[:n_v] = True
    return y


def _ids(p: int) -> list[str]:
    return [f"c{j}" for j in range(p)]


def _base_wave(n_t=101, freq=2.0, phase=0.0):
    t = np.linspace(0, 1, n_t)
    return np.sin(2 * np.pi * freq * t + phase)


def test_shared_shape_different_amplitude_detected():
    """Victims share shape with different amplitudes — P0.1-style magnitude miss."""
    rng = np.random.default_rng(0)
    n_v, n_c, n_curves, n_t = 17, 14, 8, 101
    shape_v = _base_wave(n_t, freq=2.0)
    shape_c = _base_wave(n_t, freq=3.5, phase=1.0)
    X = np.zeros((n_v + n_c, n_curves, n_t))
    for j in range(n_curves):
        for i in range(n_v):
            amp = rng.uniform(0.5, 4.0)
            X[i, j] = amp * shape_v + rng.normal(scale=0.05, size=n_t)
        for i in range(n_v, n_v + n_c):
            amp = rng.uniform(0.5, 4.0)
            X[i, j] = amp * shape_c + rng.normal(scale=0.05, size=n_t)
    y = _labels(n_v, n_c)
    summary, _ = run_shape_space(X, y, _ids(n_curves), n_perm=299, n_boot=100, seed=1)
    assert summary.mean_pairwise_pearson > 0.7
    assert summary.perm_p_pearson < 0.05
    assert summary.perm_p_dtw < 0.05 or summary.mean_pairwise_dtw < summary.null_mean_dtw


def test_random_shape_not_detected():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(31, 8, 101))
    y = _labels()
    summary, _ = run_shape_space(X, y, _ids(8), n_perm=299, n_boot=100, seed=2)
    assert summary.perm_p_pearson > 0.05
    assert summary.perm_p_dtw > 0.05


def test_one_outlier_moves_loso():
    n_v, n_c, n_curves, n_t = 17, 14, 4, 101
    shape = _base_wave(n_t, freq=2.0)
    other = _base_wave(n_t, freq=5.0, phase=2.0)
    X = np.zeros((n_v + n_c, n_curves, n_t))
    for j in range(n_curves):
        X[1:n_v, j] = shape
        X[0, j] = other  # outlier victim
        X[n_v:, j] = other * 0.3
    y = _labels(n_v, n_c)
    Z = zscore_curves(X)
    from gait_research.similarity.shape_space import build_pairwise_banks

    banks = build_pairwise_banks(Z)
    loso = loso_shape_stats(banks, y)
    assert loso["loso_pearson"][0] > loso["full_pearson"] + 0.05


def test_amplitude_only_shared_not_shape():
    """Same shape everyone; victims only larger amplitude → must NOT detect after z-score."""
    rng = np.random.default_rng(3)
    n_v, n_c, n_curves, n_t = 17, 14, 6, 101
    shape = _base_wave(n_t, freq=2.0)
    X = np.zeros((n_v + n_c, n_curves, n_t))
    for j in range(n_curves):
        for i in range(n_v):
            # proportional noise so SNR (not absolute noise) is matched across amplitudes
            amp = rng.uniform(3.0, 6.0)
            X[i, j] = amp * (shape + rng.normal(scale=0.02, size=n_t))
        for i in range(n_v, n_v + n_c):
            amp = rng.uniform(0.4, 1.0)
            X[i, j] = amp * (shape + rng.normal(scale=0.02, size=n_t))
    y = _labels(n_v, n_c)
    summary, _ = run_shape_space(X, y, _ids(n_curves), n_perm=299, n_boot=100, seed=4)
    # after z-score all nearly identical → any group of 17 equally similar
    assert summary.perm_p_pearson > 0.05
    assert summary.perm_p_dtw > 0.05


def test_zscore_strips_amplitude():
    a = _base_wave()
    b = 5.0 * a
    Za = zscore_curves(a[None, None, :])[0, 0]
    Zb = zscore_curves(b[None, None, :])[0, 0]
    np.testing.assert_allclose(Za, Zb, atol=1e-10)
    assert pearson_sim(Za, Zb) == pytest.approx(1.0)


def test_dtw_identical_zero():
    a = _base_wave()
    assert dtw_distance(a, a) == pytest.approx(0.0, abs=1e-9)
    assert dtw_distance(a, a + 10) > 0  # before z-score; amplitude matters for raw DTW


def test_residualize_curves_shape():
    rng = np.random.default_rng(5)
    X = rng.normal(size=(31, 3, 101))
    h = np.linspace(150, 180, 31)
    X[:, 0, :] += (h - h.mean())[:, None] * 0.1
    Xr = residualize_curves(X, h)
    assert Xr.shape == X.shape
    # height-driven channel should shrink correlation with height
    corr_pre = np.corrcoef(X[:, 0, 50], h)[0, 1]
    corr_post = np.corrcoef(Xr[:, 0, 50], h)[0, 1]
    assert abs(corr_post) < abs(corr_pre) * 0.2 + 0.05
