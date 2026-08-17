"""Synthetic + Phase-1 boundary tests for P0.4 event-phase localization."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from gait_research.similarity.event_phases import (
    build_subject_phase_feature_matrix,
    cycle_phase_bounds_pct,
    frame_to_pct,
    pct_to_index,
    run_event_phase_battery,
    window_agg,
)
from gait_research.similarity.shape_space import load_preregistered_curves

ROOT = Path(__file__).resolve().parents[2]


def _labels(n_v=17, n_c=14):
    y = np.zeros(n_v + n_c, dtype=bool)
    y[:n_v] = True
    return y


def test_phase_boundaries_match_phase1_inventory():
    inv = pd.read_csv(ROOT / "results" / "phase1" / "gait_cycle_inventory.csv")
    row = inv.iloc[0]
    b = cycle_phase_bounds_pct(row)
    start, end = float(row.initial_contact_frame), float(row.next_contact_frame)
    assert b["loading_response"][0] == pytest.approx(0.0)
    assert b["loading_response"][1] == pytest.approx(
        frame_to_pct(row.opposite_foot_off_frame, start, end)
    )
    assert b["pre_swing"][0] == pytest.approx(frame_to_pct(row.opposite_contact_frame, start, end))
    assert b["swing"][1] == pytest.approx(100.0)
    # all 880 cycles: strict order
    for r in inv.itertuples(index=False):
        bb = cycle_phase_bounds_pct(pd.Series(r._asdict()))
        edges = [
            bb["loading_response"][0],
            bb["loading_response"][1],
            bb["mid_stance"][1],
            bb["terminal_stance"][1],
            bb["pre_swing"][1],
            bb["swing"][1],
        ]
        assert edges == sorted(edges)
        assert edges[-1] == pytest.approx(100.0)


def test_window_agg_localized_slice():
    t = np.linspace(0, 100, 101)
    series = np.zeros(101)
    # spike only in ~0–15% (loading-like)
    series[pct_to_index(0) : pct_to_index(15)] = 10.0
    assert window_agg(series, 0.0, 15.0, "mean") == pytest.approx(10.0)
    assert window_agg(series, 40.0, 60.0, "mean") == pytest.approx(0.0)
    assert window_agg(series, 0.0, 15.0, "rom") == pytest.approx(0.0)  # flat spike plateau


def test_signal_localized_to_one_phase_detected():
    """Shared elevation only in loading_response mean → that cell should be strongest."""
    rng = np.random.default_rng(0)
    n_v, n_c = 17, 14
    phases = ["loading_response", "mid_stance", "terminal_stance", "pre_swing", "swing"]
    curves = [f"c{i}" for i in range(4)]
    aggs = ["mean", "rom"]
    names = [f"{p}__{c}__{a}" for p in phases for c in curves for a in aggs]
    X = rng.normal(scale=0.3, size=(n_v + n_c, len(names)))
    # victims share a large offset only on loading_response × c0 × mean
    target = names.index("loading_response__c0__mean")
    X[:n_v, target] = 5.0 + rng.normal(scale=0.05, size=n_v)
    X[n_v:, target] = rng.normal(scale=0.3, size=n_c)
    y = _labels(n_v, n_c)
    summary, details = run_event_phase_battery(
        X, names, y, phases, n_perm=299, seed=1
    )
    cell = details["cell_table"]
    hit = cell[(cell["feature"] == "loading_response__c0__mean") & (cell["test_type"] == "deviation_cosine")]
    other = cell[
        (cell["phase"] != "loading_response")
        & (cell["test_type"] == "deviation_cosine")
        & (cell["aggregation"] == "mean")
    ]
    assert float(hit["raw_p"].iloc[0]) < 0.05
    assert float(hit["raw_p"].iloc[0]) <= float(other["raw_p"].min())
    assert summary.n_fdr_family == len(names) * 2


def test_null_random_features_few_fdr():
    rng = np.random.default_rng(2)
    phases = ["loading_response", "mid_stance", "terminal_stance", "pre_swing", "swing"]
    curves = [f"c{i}" for i in range(3)]
    aggs = ["mean", "rom"]
    names = [f"{p}__{c}__{a}" for p in phases for c in curves for a in aggs]
    X = rng.normal(size=(31, len(names)))
    y = _labels()
    summary, details = run_event_phase_battery(X, names, y, phases, n_perm=199, seed=3)
    # under pure noise, FDR survivors should be rare
    assert summary.n_fdr_le_0_05 == 0 or details["cell_table"]["raw_p"].min() > 0.001


def test_one_outlier_moves_window_loso_cosine():
    n_v, n_c, d = 17, 14, 8
    X = np.zeros((n_v + n_c, d))
    y = _labels(n_v, n_c)
    X[1:n_v, 0] = 1.0
    X[0, 0] = -1.0
    from gait_research.similarity.deviation import loso_mean_pairwise_cosine

    loso = loso_mean_pairwise_cosine(X, y)
    assert loso["loso_values"][0] > loso["full_observed"] + 0.05


def test_build_matrix_from_phase1_smoke():
    """Smoke: extract real Phase 1 window features for one subject’s worth of structure."""
    from gait_research.trajectories.load import load_normalized_cube

    loaded = load_normalized_cube(ROOT)
    curves = load_preregistered_curves(ROOT / "results" / "similarity" / "p03_shape" / "preregistered_curves.json")
    # use first 2 subjects only for speed
    inv = loaded["inventory"]
    keep_ids = sorted(inv["subject_id"].astype(str).unique())[:2]
    mask = inv["subject_id"].astype(str).isin(keep_ids)
    inv2 = inv.loc[mask].reset_index(drop=True)
    cube2 = loaded["cube"][mask.to_numpy()]
    built = build_subject_phase_feature_matrix(
        cube2,
        inv2,
        loaded["signals"],
        curves,
        ["loading_response", "swing"],
        ["mean", "rom"],
    )
    assert built["X"].shape[0] == 2
    assert built["X"].shape[1] == 2 * 12 * 2
    assert np.isfinite(built["X"]).all()
