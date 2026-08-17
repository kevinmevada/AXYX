import numpy as np
import pandas as pd

from gait_research.phenotypes.clustering import evaluate_k_grid, hierarchical_labels, select_k
from gait_research.phenotypes.dimensionality import fit_pca
from gait_research.phenotypes.stability import bootstrap_ari, stability_grid


def test_pca_deterministic():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(31, 12))
    a = fit_pca(X, seed=1)
    b = fit_pca(X, seed=1)
    np.testing.assert_allclose(a["scores"], b["scores"], atol=1e-10)
    assert a["n_keep"] >= 2
    assert np.all(np.diff(a["cumulative"]) >= -1e-12)


def test_hierarchical_reproducible():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(31, 8))
    a = hierarchical_labels(X, 3)
    b = hierarchical_labels(X, 3)
    np.testing.assert_array_equal(a, b)


def test_separated_blobs_recover_structure():
    rng = np.random.default_rng(2)
    a = rng.normal(size=(10, 6))
    b = rng.normal(size=(10, 6)) + 8.0
    c = rng.normal(size=(11, 6)) + np.array([8.0, 0, 8, 0, 8, 0])
    X = np.vstack([a, b, c])
    labels = hierarchical_labels(X, 3)
    assert len(np.unique(labels)) == 3
    metrics, assignments = evaluate_k_grid(X, ks=(2, 3, 4), seed=0)
    stability, _ = stability_grid(X, {("hierarchical", k): assignments[("hierarchical", k)] for k in (2, 3, 4)}, np.array([f"S{i}" for i in range(31)]), seed=0)
    # attach dummy kmeans-less stability rows already in full grid; here only hier
    choice = select_k(metrics[metrics["method"] == "hierarchical"], stability)
    # well-separated blobs should at least pass some k or have high silhouette at 3
    sil3 = metrics[(metrics.method == "hierarchical") & (metrics.k == 3)]["silhouette"].iloc[0]
    assert sil3 > 0.4
    mean_ari, _ = bootstrap_ari(X, labels, 3, n_boot=20, seed=0)
    assert mean_ari > 0.5


def test_isotropic_noise_not_forced_as_phenotype():
    rng = np.random.default_rng(3)
    X = rng.normal(size=(31, 10))
    metrics, assignments = evaluate_k_grid(X, ks=(2, 3, 4), seed=0)
    stability, _ = stability_grid(
        X,
        {key: assignments[key] for key in assignments if key[0] == "hierarchical"},
        np.array([f"S{i}" for i in range(31)]),
        seed=0,
    )
    choice = select_k(metrics, stability)
    assert choice["k"] is None
    assert choice["reason"] == "no_stable_phenotype_structure"
