import numpy as np
import pandas as pd

from gait_research.statistics.engine import _rank_score, _signature_flag
from gait_research.statistics.group_comparison import compare_groups, directional_consistency
from gait_research.statistics.robustness import permutation_cliffs


def _two_groups(feat_v, feat_c):
    v = [{"subject_id": f"V{i}", "victimized": "Y", "feat": float(x)} for i, x in enumerate(feat_v)]
    c = [{"subject_id": f"C{i}", "victimized": "N", "feat": float(x)} for i, x in enumerate(feat_c)]
    return pd.DataFrame(v + c)


def test_compare_groups_direction_and_consistency():
    df = _two_groups(np.arange(17, dtype=float) + 10, np.arange(14, dtype=float))
    out = compare_groups(df, ["feat"])
    row = out.iloc[0]
    assert row["n_subjects"] == 31
    assert row["n_victims"] == 17
    assert row["n_controls"] == 14
    assert row["direction"] == "VICTIMS_HIGHER"
    assert row["cliffs_delta"] > 0.9
    assert row["victim_consistency"] >= 0.9


def test_directional_consistency_six_of_seventeen():
    victims = np.concatenate([np.array([6.0, 7, 8, 9, 10, 11]), np.zeros(11)])
    assert directional_consistency(victims, 5.0, "VICTIMS_HIGHER") == 6 / 17


def test_permutation_unit_is_subject_not_cycle():
    df = _two_groups(np.linspace(10, 20, 17), np.linspace(0, 5, 14))
    out = permutation_cliffs(df, ["feat"], n_perm=19, seed=1)
    assert out.iloc[0]["unit"] == "subject"
    assert out.iloc[0]["n_perm"] == 19
    assert 0 < out.iloc[0]["perm_p"] <= 1


def test_ranking_is_not_pvalue_only():
    weak_p = pd.Series(
        {
            "cliffs_delta": 0.05,
            "fdr_q": 0.001,
            "loso_direction_agreement": 1.0,
            "victim_consistency": 0.55,
            "family": "kinematic",
            "n_victims": 17,
            "n_controls": 14,
        }
    )
    strong_effect = pd.Series(
        {
            "cliffs_delta": 0.55,
            "fdr_q": 0.08,
            "loso_direction_agreement": 0.95,
            "victim_consistency": 0.80,
            "family": "kinematic",
            "n_victims": 17,
            "n_controls": 14,
        }
    )
    assert _rank_score(strong_effect) > _rank_score(weak_p)
    assert _signature_flag(weak_p) == "exploratory"
    assert _signature_flag(strong_effect) == "signature_candidate"
