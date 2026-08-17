import pandas as pd
import pytest

from gait_research.features.context import LABEL_COLUMNS
from gait_research.phenotypes.clustering import select_k
from gait_research.phenotypes.representation import assert_no_labels, robust_scale
import numpy as np


def test_assert_no_labels_rejects_victimized():
    df = pd.DataFrame({"subject_id": ["S1"], "victimized": ["Y"]})
    with pytest.raises(RuntimeError, match="label leakage"):
        assert_no_labels(df)


def test_assert_no_labels_rejects_victim_derived_name():
    df = pd.DataFrame({"subject_id": ["S1"], "victim_score": [1.0]})
    with pytest.raises(RuntimeError, match="label leakage"):
        assert_no_labels(df)


def test_label_columns_constant_matches_phase2():
    assert "victimized" in LABEL_COLUMNS


def test_select_k_signature_has_no_label_argument():
    import inspect

    params = inspect.signature(select_k).parameters
    assert "victimized" not in params
    assert "labels" not in params
    assert "y" not in params


def test_robust_scale_is_label_blind_and_deterministic():
    X = np.array([[0.0, 10.0], [1.0, 20.0], [2.0, 30.0], [100.0, 40.0]])
    z1, med, iqr = robust_scale(X)
    z2, _, _ = robust_scale(X)
    np.testing.assert_allclose(z1, z2)
    np.testing.assert_allclose(med, np.median(X, axis=0))
    assert z1.shape == X.shape
