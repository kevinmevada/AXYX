import numpy as np

from gait_research.statistics.effect_sizes import cliffs_delta, cliffs_delta_label


def test_cliffs_delta_complete_separation_positive():
    x = np.array([10.0, 11.0, 12.0])
    y = np.array([1.0, 2.0, 3.0])
    assert cliffs_delta(x, y) == 1.0


def test_cliffs_delta_complete_separation_negative():
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([10.0, 11.0, 12.0])
    assert cliffs_delta(x, y) == -1.0


def test_cliffs_delta_ties_zero():
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([1.0, 2.0, 3.0])
    assert cliffs_delta(x, y) == 0.0


def test_cliffs_magnitude_thresholds():
    assert cliffs_delta_label(0.10) == "negligible"
    assert cliffs_delta_label(0.20) == "small"
    assert cliffs_delta_label(0.40) == "medium"
    assert cliffs_delta_label(0.50) == "large"
