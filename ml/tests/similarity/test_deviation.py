"""Synthetic sanity tests for P0.1 deviation-direction alignment."""

from __future__ import annotations

import numpy as np
import pytest

from gait_research.similarity.deviation import (
    control_referenced_deviations,
    loso_mean_pairwise_cosine,
    mean_pairwise_cosine,
    permute_mean_pairwise_cosine,
    residualize_columns,
    run_deviation_alignment,
)


def _labels(n_v=17, n_c=14):
    y = np.zeros(n_v + n_c, dtype=bool)
    y[:n_v] = True
    return y


def test_shared_direction_detected():
    """Victims share a common offset from controls → high cosine, low perm p."""
    rng = np.random.default_rng(0)
    n_v, n_c, d = 17, 14, 27
    direction = rng.normal(size=d)
    direction /= np.linalg.norm(direction)
    controls = rng.normal(scale=0.3, size=(n_c, d))
    # victims = control-like noise + shared direction * random positive scale
    scales = rng.uniform(0.8, 2.5, size=n_v)
    victims = rng.normal(scale=0.3, size=(n_v, d)) + scales[:, None] * direction
    X = np.vstack([victims, controls])
    y = _labels(n_v, n_c)
    summary, details = run_deviation_alignment(X, y, n_perm=499, n_boot=200, seed=1)
    assert summary.mean_pairwise_cosine > 0.5
    assert summary.perm_p < 0.05
    assert summary.consistency_frac_positive > 0.8
    assert summary.loso_pass


def test_isotropic_not_detected():
    """No shared structure → should NOT reject null (false-positive check)."""
    rng = np.random.default_rng(1)
    X = rng.normal(size=(31, 27))
    y = _labels()
    summary, _ = run_deviation_alignment(X, y, n_perm=499, n_boot=200, seed=2)
    assert 0 < summary.perm_p <= 1
    # not a significant discovery under this seed
    assert summary.perm_p > 0.05


def test_one_outlier_fails_loso():
    """Anti-aligned victim must move the LOSO statistic (proves LOSO is live)."""
    n_v, n_c, d = 17, 14, 8
    X = np.zeros((n_v + n_c, d))
    y = _labels(n_v, n_c)
    X[1:n_v, 0] = 1.0
    X[0, 0] = -1.0
    loso = loso_mean_pairwise_cosine(X, y)
    # dropping the anti-aligned victim raises mean pairwise cosine among remaining victims
    assert loso["loso_values"][0] > loso["full_observed"] + 0.05
    # dropping an aligned victim should not raise it as much
    assert loso["loso_values"][0] > np.nanmean(loso["loso_values"][1:n_v])


def test_height_only_dies_after_residualization():
    """If 'alignment' is only height-driven, residuals must kill the signal."""
    rng = np.random.default_rng(3)
    n_v, n_c, d = 17, 14, 15
    height = np.linspace(150, 175, n_v + n_c)
    # make victims systematically taller
    height[:n_v] = np.linspace(165, 180, n_v)
    height[n_v:] = np.linspace(150, 162, n_c)
    # representation is pure function of height + tiny noise
    basis = rng.normal(size=d)
    basis /= np.linalg.norm(basis)
    X = (height - height.mean())[:, None] * basis + rng.normal(scale=0.01, size=(n_v + n_c, d))
    y = _labels(n_v, n_c)
    pre, _ = run_deviation_alignment(X, y, n_perm=299, n_boot=100, seed=4)
    X_res = residualize_columns(X, height)
    post, _ = run_deviation_alignment(
        X_res, y, n_perm=299, n_boot=100, seed=4, residualized=True, residual_covariates=("height",)
    )
    # pre may look aligned; post must not be a significant shared-direction claim
    assert post.perm_p > 0.05 or post.mean_pairwise_cosine < 0.15
    assert abs(post.mean_pairwise_cosine) < abs(pre.mean_pairwise_cosine) + 0.05


def test_control_mean_excludes_victims():
    X = np.arange(30, dtype=float).reshape(10, 3)
    y = np.array([True] * 5 + [False] * 5)
    D, mu = control_referenced_deviations(X, y)
    np.testing.assert_allclose(mu, X[~y].mean(axis=0))
    np.testing.assert_allclose(D[~y].mean(axis=0), 0.0, atol=1e-12)


def test_mean_pairwise_cosine_identical_rows():
    D = np.ones((5, 4))
    assert mean_pairwise_cosine(D) == pytest.approx(1.0)


def test_permutation_unit_is_subject_sized():
    rng = np.random.default_rng(5)
    X = rng.normal(size=(31, 10))
    y = _labels()
    out = permute_mean_pairwise_cosine(X, y, n_perm=50, seed=1)
    assert out["unit"] == "subject"
    assert out["n_perm"] == 50
    assert out["null"].shape == (50,)
