import numpy as np

from gait_research.statistics.multiple_testing import benjamini_hochberg


def test_benjamini_hochberg_known_example():
    p = np.array([0.01, 0.04, 0.03, 0.005])
    q = benjamini_hochberg(p)
    expected = np.array([0.02, 0.04, 0.04, 0.02])
    np.testing.assert_allclose(q, expected, atol=1e-12)


def test_benjamini_hochberg_preserves_nan():
    p = np.array([0.01, np.nan, 0.20])
    q = benjamini_hochberg(p)
    assert np.isnan(q[1])
    assert np.isfinite(q[0]) and np.isfinite(q[2])
    assert q[0] <= q[2]
