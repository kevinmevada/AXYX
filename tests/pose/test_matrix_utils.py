"""Matrix utility tests."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.pose.matrix_utils import (
    compose_trs,
    decompose_trs,
    identity_matrix,
    invert_affine,
    is_finite,
    is_rotation_orthogonal,
    is_singular,
    is_unit_quat,
    quat_normalize,
)


def test_identity_invert() -> None:
    eye = identity_matrix()
    assert np.allclose(invert_affine(eye), eye)


def test_compose_decompose() -> None:
    m = compose_trs((1, 2, 3), (0, 0, 0, 1), (1, 1, 1))
    t, q, s = decompose_trs(m)
    assert np.allclose(t, (1, 2, 3))
    assert is_unit_quat(q)


def test_singular() -> None:
    m = identity_matrix()
    m[0, 0] = 0.0
    m[1, 1] = 0.0
    m[2, 2] = 0.0
    assert is_singular(m)


def test_nan_not_finite() -> None:
    m = identity_matrix()
    m[0, 0] = np.nan
    assert not is_finite(m)


def test_quat_normalize_zero() -> None:
    q = quat_normalize((0, 0, 0, 0))
    assert np.allclose(q, (0, 0, 0, 1))


def test_ortho_identity() -> None:
    assert is_rotation_orthogonal(identity_matrix())
