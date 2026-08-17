import numpy as np
import pandas as pd

from gait_research.within_victim.subgroups import discover_victim_subgroups
from gait_research.phenotypes.clustering import hierarchical_labels


def test_two_victim_blobs_can_be_stable():
    rng = np.random.default_rng(7)
    a = rng.normal(size=(8, 5))
    b = rng.normal(size=(9, 5)) + 8.0
    X = np.vstack([a, b])
    ids = np.array([f"V{i}" for i in range(17)])
    out = discover_victim_subgroups(X, ids, seed=0)
    # well-separated data should either select k=2 or at least have high silhouette at 2
    sil2 = out["metrics"][(out["metrics"].method == "hierarchical") & (out["metrics"].k == 2)]["silhouette"].iloc[0]
    assert sil2 > 0.4
    labs = hierarchical_labels(X, 2)
    assert len(np.unique(labs)) == 2


def test_noise_victims_not_forced():
    rng = np.random.default_rng(8)
    X = rng.normal(size=(17, 8))
    ids = np.array([f"V{i}" for i in range(17)])
    out = discover_victim_subgroups(X, ids, seed=1)
    if out["choice"]["k"] is not None:
        # if a k passes, sizes must meet the rule
        sizes = out["assignments"]["subgroup"].value_counts()
        assert sizes.min() >= 4
    else:
        assert (out["assignments"]["subgroup"] == "none_stable").all()
    assert "victimized" not in out["assignments"].columns
    assert out["assignments"].shape[0] == 17
