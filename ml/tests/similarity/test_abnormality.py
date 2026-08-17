"""Synthetic sanity tests for P0.2 abnormality-set Jaccard overlap."""

from __future__ import annotations

import numpy as np
import pytest

from gait_research.similarity.abnormality import (
    build_exceedance,
    control_bands,
    exceedance_matrix,
    jaccard,
    loso_mean_pairwise_jaccard,
    mean_pairwise_jaccard,
    permute_mean_pairwise_jaccard,
    run_abnormality_overlap,
)
from gait_research.similarity.deviation import residualize_columns


def _labels(n_v=17, n_c=14):
    y = np.zeros(n_v + n_c, dtype=bool)
    y[:n_v] = True
    return y


def _names(p: int) -> list[str]:
    return [f"f{j}" for j in range(p)]


def test_shared_abnormality_set_detected():
    """Victims share the same out-of-band features → high Jaccard, low perm p."""
    rng = np.random.default_rng(0)
    n_v, n_c, p = 17, 14, 30
    # controls ~ N(0,1); victims share exceedances on first 8 features
    controls = rng.normal(size=(n_c, p))
    victims = rng.normal(size=(n_v, p))
    victims[:, :8] = 5.0  # far above control 90th
    X = np.vstack([victims, controls])
    y = _labels(n_v, n_c)
    summary, _ = run_abnormality_overlap(X, y, _names(p), n_perm=499, n_boot=200, seed=1)
    assert summary.mean_pairwise_jaccard > 0.4
    assert summary.perm_p < 0.05
    assert summary.n_features_fdr_le_0_10 >= 1


def test_independent_exceedance_not_detected():
    """Random / independent exceedances → should NOT reject null."""
    rng = np.random.default_rng(1)
    X = rng.normal(size=(31, 30))
    y = _labels()
    summary, _ = run_abnormality_overlap(X, y, _names(30), n_perm=499, n_boot=200, seed=2)
    assert 0 < summary.perm_p <= 1
    assert summary.perm_p > 0.05


def test_one_outlier_moves_loso_jaccard():
    """Victim with a disjoint abnormality set raises LOSO Jaccard when dropped."""
    n_v, n_c, p = 17, 14, 20
    X = np.zeros((n_v + n_c, p))
    y = _labels(n_v, n_c)
    # controls stay at 0; shared victim set on features 0–4
    X[1:n_v, 0:5] = 10.0
    # outlier victim abnormal on disjoint features 10–14
    X[0, 10:15] = 10.0
    loso = loso_mean_pairwise_jaccard(X, y)
    assert loso["loso_values"][0] > loso["full_observed"] + 0.05
    assert loso["loso_values"][0] > np.nanmean(loso["loso_values"][1:n_v])


def test_height_only_dies_after_residualization():
    """Feature abnormal only via height must lose shared-set signal after residualization."""
    rng = np.random.default_rng(3)
    n_v, n_c, p = 17, 14, 20
    height = np.zeros(n_v + n_c)
    height[:n_v] = np.linspace(170, 185, n_v)
    height[n_v:] = np.linspace(150, 162, n_c)
    # feature 0 is pure height; others noise
    X = rng.normal(scale=0.05, size=(n_v + n_c, p))
    X[:, 0] = (height - height.mean()) / height.std()
    y = _labels(n_v, n_c)
    pre, _ = run_abnormality_overlap(X, y, _names(p), n_perm=299, n_boot=100, seed=4)
    X_res = residualize_columns(X, height)
    post, details_post = run_abnormality_overlap(
        X_res,
        y,
        _names(p),
        n_perm=299,
        n_boot=100,
        seed=4,
        residualized=True,
        residual_covariates=("height",),
    )
    # after residualization, feature 0 should not drive a shared-set claim
    assert post.perm_p > 0.05 or post.mean_pairwise_jaccard <= post.null_mean
    assert details_post["feature_table"].loc[
        details_post["feature_table"]["feature"] == "f0", "fdr_q"
    ].iloc[0] > 0.10 or post.perm_p > 0.05
    # residualization should not inflate Jaccard relative to a height-driven pre
    assert post.mean_pairwise_jaccard <= pre.mean_pairwise_jaccard + 0.05


def test_control_band_excludes_victims():
    X = np.arange(30, dtype=float).reshape(10, 3)
    y = np.array([True] * 5 + [False] * 5)
    p_lo, p_hi = control_bands(X, y)
    ctrl = X[~y]
    np.testing.assert_allclose(p_lo, np.percentile(ctrl, 10, axis=0))
    np.testing.assert_allclose(p_hi, np.percentile(ctrl, 90, axis=0))


def test_jaccard_identical_and_disjoint():
    a = np.array([1, 1, 0, 0])
    b = np.array([1, 1, 0, 0])
    c = np.array([0, 0, 1, 1])
    assert jaccard(a, b) == pytest.approx(1.0)
    assert jaccard(a, c) == pytest.approx(0.0)
    assert mean_pairwise_jaccard(np.vstack([a, b, a])) == pytest.approx(1.0)


def test_exceedance_outside_band():
    X = np.array([[0.0, 5.0], [0.0, -5.0], [0.0, 0.0]])
    p_lo = np.array([-1.0, -1.0])
    p_hi = np.array([1.0, 1.0])
    B = exceedance_matrix(X, p_lo, p_hi)
    np.testing.assert_array_equal(B[:, 0], [0, 0, 0])
    np.testing.assert_array_equal(B[:, 1], [1, 1, 0])


def test_permutation_unit_is_subject_sized():
    rng = np.random.default_rng(5)
    X = rng.normal(size=(31, 12))
    y = _labels()
    out = permute_mean_pairwise_jaccard(X, y, n_perm=50, seed=1)
    assert out["unit"] == "subject"
    assert out["n_perm"] == 50
    assert out["null"].shape == (50,)
    built = build_exceedance(X, y)
    assert built["B"].shape == (31, 12)
