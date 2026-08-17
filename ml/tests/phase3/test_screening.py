import numpy as np
import pandas as pd
import pytest

from gait_research.statistics.screening import analysis_columns, quality_screen, redundancy_clusters


def test_analysis_columns_default_to_median_and_var_sym():
    df = pd.DataFrame(
        {
            "subject_id": ["S1"],
            "n_cycles": [1],
            "A__median": [1.0],
            "A__mean": [1.0],
            "A__std": [0.1],
            "A__cv": [0.1],
            "A__n": [4],
            "var_A": [0.2],
            "sym_A": [0.3],
        }
    )
    cols = analysis_columns(df)
    assert cols == ["A__median", "var_A", "sym_A"]


def test_quality_screen_rejects_labels():
    df = pd.DataFrame({"subject_id": ["S1"], "A__median": [1.0], "victimized": ["Y"]})
    with pytest.raises(RuntimeError, match="must not receive group labels"):
        quality_screen(df, ["A__median"])


def test_quality_screen_drops_constant_and_duplicate():
    rng = np.random.default_rng(0)
    n = 31
    good = rng.normal(size=n)
    df = pd.DataFrame(
        {
            "subject_id": [f"S{i}" for i in range(n)],
            "good__median": good,
            "const__median": np.ones(n),
            "dup__median": good.copy(),
        }
    )
    screen, keep = quality_screen(df, ["good__median", "const__median", "dup__median"], min_n=31)
    assert keep == ["good__median"]
    reasons = dict(zip(screen["feature"], screen["reasons"]))
    assert "constant" in reasons["const__median"]
    assert "duplicated:good__median" in reasons["dup__median"]


def test_redundancy_clusters_reject_labels_and_keep_rom_rep():
    n = 31
    x = np.linspace(0, 1, n)
    df = pd.DataFrame(
        {
            "subject_id": [f"S{i}" for i in range(n)],
            "knee_ax1_rom__median": x,
            "knee_ax1_max__median": x + 0.001,
            "knee_ax1_phase_0_10_mean__median": np.linspace(2, 3, n),
            "victimized": ["Y"] * n,
        }
    )
    with pytest.raises(RuntimeError, match="must not receive group labels"):
        redundancy_clusters(df, ["knee_ax1_rom__median"])
    unlabeled = df.drop(columns=["victimized"])
    clusters, reps = redundancy_clusters(
        unlabeled,
        ["knee_ax1_rom__median", "knee_ax1_max__median", "knee_ax1_phase_0_10_mean__median"],
        rho=0.90,
    )
    assert "knee_ax1_rom__median" in reps
    rom_cluster = clusters.loc[clusters["representative"] == "knee_ax1_rom__median"].iloc[0]
    assert "knee_ax1_max__median" in rom_cluster["members"]
