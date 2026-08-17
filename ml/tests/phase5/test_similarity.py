import numpy as np
import pandas as pd
import pytest

from gait_research.within_victim.similarity import mean_pairwise_distance, within_group_similarity
from gait_research.within_victim.neighbors import nn_permutation
from gait_research.within_victim.vs_controls import centroid_perm_p
from gait_research.phenotypes.representation import assert_no_labels


def test_tight_group_more_similar_than_chance():
    rng = np.random.default_rng(0)
    victims = rng.normal(scale=0.2, size=(17, 6))
    others = rng.normal(loc=5.0, scale=1.0, size=(14, 6))
    X = np.vstack([victims, others])
    mask = np.array([True] * 17 + [False] * 14)
    out = within_group_similarity(X, mask, n_perm=199, seed=1)
    assert out["unit"] == "subject"
    assert out["n_group"] == 17
    assert out["observed_mean_pairwise_distance"] < out["null_mean"]
    assert out["perm_p"] < 0.05


def test_isotropic_not_forced_similar():
    rng = np.random.default_rng(4)
    X = rng.normal(size=(31, 8))
    mask = np.zeros(31, dtype=bool)
    mask[:17] = True
    out = within_group_similarity(X, mask, n_perm=199, seed=2)
    assert 0 < out["perm_p"] <= 1
    assert abs(out["observed_mean_pairwise_distance"] - out["null_mean"]) < 3 * out["null_sd"]


def test_nn_and_centroid_units_are_subject():
    rng = np.random.default_rng(5)
    X = np.vstack([rng.normal(size=(17, 4)), rng.normal(loc=6, size=(14, 4))])
    y = np.array(["Y"] * 17 + ["N"] * 14)
    nn = nn_permutation(X, y, n_perm=99, seed=1)
    assert nn["unit"] == "subject"
    assert nn["obs_frac_nn_victim"] > 0.5
    dist, p = centroid_perm_p(X[:17], X[17:], n_perm=99, seed=1)
    assert dist > 0
    assert p < 0.05


def test_mean_pairwise_two_points():
    X = np.array([[0.0, 0.0], [3.0, 4.0]])
    assert mean_pairwise_distance(X) == 5.0


def test_compact_names_cannot_include_victim():
    df = pd.DataFrame({"victim_pc1": [1.0]})
    with pytest.raises(RuntimeError):
        assert_no_labels(df)
