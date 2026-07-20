"""Unit tests for Bone and Transform."""

from __future__ import annotations

import numpy as np
import pytest

from motion_engine.rendering.avatar.skeleton import Bone, Transform
from motion_engine.rendering.avatar.skeleton.transforms import (
    compose_matrix,
    decompose_matrix,
    identity_matrix,
    is_uniform_scale,
    quat_normalize,
)


def test_transform_identity_matrix() -> None:
    t = Transform.identity()
    m = t.to_matrix()
    assert np.allclose(m, identity_matrix())


def test_transform_roundtrip() -> None:
    t = Transform(translation=(1.0, 2.0, 3.0), rotation_xyzw=(0.0, 0.0, 0.0, 1.0), scale=(2.0, 2.0, 2.0))
    m = t.to_matrix()
    t2 = Transform.from_matrix(m)
    assert np.allclose(t2.translation, (1.0, 2.0, 3.0))
    assert np.allclose(t2.scale, (2.0, 2.0, 2.0), atol=1e-6)


def test_compose_matches_matrix() -> None:
    a = Transform.from_translation((1, 0, 0))
    b = Transform.from_translation((0, 2, 0))
    c = a.compose(b)
    assert np.allclose(c.to_matrix(), a.to_matrix() @ b.to_matrix())


def test_quat_normalize_zero() -> None:
    q = quat_normalize((0, 0, 0, 0))
    assert np.allclose(q, (0, 0, 0, 1))


def test_non_uniform_scale_flag() -> None:
    t = Transform(scale=(1.0, 2.0, 1.0))
    assert t.has_non_uniform_scale
    assert not is_uniform_scale((1.0, 2.0, 1.0))


def test_bone_properties() -> None:
    b = Bone(
        index=0,
        name="pelvis",
        parent_index=None,
        local_transform=Transform.from_translation((0, 1, 0)),
        world_transform=identity_matrix(),
        inverse_bind=identity_matrix(),
    )
    assert b.is_root
    assert b.is_leaf
    assert b.translation == (0.0, 1.0, 0.0)
    assert b.has_inverse_bind
    assert b.id == 0


def test_bone_with_children_immutable() -> None:
    b = Bone(index=0, name="r", parent_index=None)
    b2 = b.with_children((1, 2))
    assert b.children == ()
    assert b2.children == (1, 2)
    assert not b2.is_leaf


def test_decompose_compose_stable() -> None:
    m = compose_matrix((3, 4, 5), (0, 0, 0, 1), (1, 1, 1))
    t, q, s = decompose_matrix(m)
    assert np.allclose(t, (3, 4, 5))
    assert np.allclose(s, (1, 1, 1), atol=1e-6)
