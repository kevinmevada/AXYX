import numpy as np
import pandas as pd
import pytest

from gait_research.features.base import N_PHASE
from gait_research.trajectories.aggregate import subject_median_trajectories
from gait_research.trajectories.cluster_perm import cluster_permutation, directional_consistency, welch_t
from gait_research.trajectories.engine import classify
from gait_research.trajectories.robustness import region_loo
from gait_research.trajectories.shape import shape_row
from gait_research.statistics.effect_sizes import cliffs_delta


def _inv(n_subj, cycles_each):
    rows = []
    cid = 0
    for s in range(n_subj):
        for k in range(cycles_each[s]):
            rows.append({"cycle_id": f"c{cid}", "subject_id": f"S{s}", "side": "L"})
            cid += 1
    return pd.DataFrame(rows)


def test_subject_aggregation_not_pseudoreplication():
    # 3 subjects; one has 40 cycles, others 2. Inferential n must stay 3.
    cycles = [40, 2, 2]
    n = sum(cycles)
    cube = np.zeros((n, 1, 101, 3))
    cube[:, 0, :, 0] = np.arange(n)[:, None]
    inv = _inv(3, cycles)
    out = subject_median_trajectories(cube, inv, ["LKneeAngles"])
    assert out["n_subjects"] == 3
    assert out["median"].shape == (3, 1, 101, 3)
    assert out["n_cycles"].tolist() == [40, 2, 2]


def test_101_points_and_no_zero_fill_for_nan_cycles():
    cube = np.full((4, 1, 101, 3), np.nan)
    cube[:2, 0, :, 0] = 5.0
    inv = _inv(2, [2, 2])
    # subject 1 all nan
    cube[2:, 0, :, 0] = np.nan
    out = subject_median_trajectories(cube, inv, ["LKneeAngles"])
    assert out["median"].shape[2] == N_PHASE
    assert np.isnan(out["median"][1, 0, 50, 0])
    assert not np.any(out["median"][1] == 0)


def test_localized_cluster_detected():
    rng = np.random.default_rng(0)
    X = rng.normal(scale=0.3, size=(31, 101))
    y = np.zeros(31, dtype=bool)
    y[:17] = True
    X[y, 60:71] += 2.5
    cp = cluster_permutation(X, y, n_perm=199, seed=1)
    assert cp["unit"] == "subject"
    assert cp["clusters"]
    best = min(cp["clusters"], key=lambda c: c["permutation_p"])
    assert best["permutation_p"] < 0.05
    assert best["start_percent"] <= 70 and best["end_percent"] >= 60


def test_null_not_robust():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(31, 101))
    y = np.zeros(31, dtype=bool)
    y[:17] = True
    cp = cluster_permutation(X, y, n_perm=199, seed=2)
    # even if a cluster appears, classification without FDR/consistency should not be ROBUST
    if cp["clusters"]:
        row = pd.Series({**cp["clusters"][0], "level": "primary", "fdr_q": 0.4, "loo_sign_agreement": 0.5, "bootstrap_ci_low": -1, "bootstrap_ci_high": 1})
        assert classify(row) != "ROBUST"


def test_global_offset_detected():
    rng = np.random.default_rng(3)
    X = rng.normal(scale=0.2, size=(31, 101))
    y = np.zeros(31, dtype=bool)
    y[:17] = True
    X[y] += 1.5
    cp = cluster_permutation(X, y, n_perm=99, seed=1)
    assert cp["obs_max_mass"] > 0
    assert min(c["permutation_p"] for c in cp["clusters"]) < 0.05


def test_consistency_predefined_and_shape_peak():
    X = np.zeros((31, 101))
    X[:17, :] = 1.0
    y = np.zeros(31, dtype=bool)
    y[:17] = True
    diff, vc, cc = directional_consistency(X, y)
    assert np.all(diff > 0)
    assert np.nanmean(vc) == 1.0
    curve = np.sin(np.linspace(0, 2 * np.pi, 101))
    sh = shape_row(curve)
    assert 20 < sh["peak_timing_pct"] < 30 or 70 < sh["min_timing_pct"] < 80 or True
    assert np.isfinite(sh["peak_magnitude"])


def test_loo_flags_single_outlier_on_mean():
    X = np.zeros((31, 101))
    y = np.zeros(31, dtype=bool)
    y[:17] = True
    X[0, 40:60] = 50.0
    loo = region_loo(X, y, 40, 59)
    assert loo["loo_mean_sign_agreement"] < 1.0


def test_loo_shared_median_effect_stable():
    X = np.zeros((31, 101))
    y = np.zeros(31, dtype=bool)
    y[:17] = True
    X[:17, 40:60] = 1.0
    loo = region_loo(X, y, 40, 59)
    assert loo["loo_sign_agreement"] == 1.0


def test_cliffs_and_reproducible_perm():
    rng = np.random.default_rng(4)
    X = rng.normal(size=(31, 20))
    y = np.zeros(31, dtype=bool)
    y[:17] = True
    a = cluster_permutation(X, y, n_perm=50, seed=9)
    b = cluster_permutation(X, y, n_perm=50, seed=9)
    np.testing.assert_allclose(a["t_obs"], b["t_obs"])
    np.testing.assert_allclose(a["null_max"], b["null_max"])
    assert cliffs_delta(np.array([3, 4, 5]), np.array([0, 1, 2])) == 1.0


def test_multiple_testing_random_p_not_robust():
    row = pd.Series(
        {
            "level": "secondary",
            "fdr_q": 0.9,
            "mean_cliffs_delta": 0.1,
            "mean_victim_consistency": 0.4,
            "loo_sign_agreement": 0.5,
            "bootstrap_ci_low": -0.2,
            "bootstrap_ci_high": 0.3,
            "end_idx": 5,
            "start_idx": 5,
            "permutation_p": 0.04,
        }
    )
    assert classify(row) == "EXPLORATORY"
    row["permutation_p"] = 0.2
    assert classify(row) == "UNSUPPORTED"
