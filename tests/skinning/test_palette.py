"""Bone / matrix palette tests."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.skinning import BonePalette, build_matrix_palette
from tests.skinning.helpers import make_bind


def test_identity_palette() -> None:
    p = BonePalette.identity(3, names=["a", "b", "c"])
    assert p.size == 3
    assert list(p.bone_indices) == [0, 1, 2]


def test_matrix_palette_bind_is_identity() -> None:
    """At bind pose, world @ ibm ≈ I → skin matrix ≈ I."""
    bind = make_bind()
    pal = build_matrix_palette(bind)
    for m in pal.matrices:
        assert np.allclose(m, np.eye(4), atol=1e-5)
