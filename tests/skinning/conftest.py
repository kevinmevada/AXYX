"""Fixtures for skinning tests."""

from __future__ import annotations

import pytest

from tests.skinning.helpers import make_bind, make_mesh_skin, make_segment_mesh


@pytest.fixture
def mesh():
    return make_segment_mesh(5)


@pytest.fixture
def bind():
    return make_bind()


@pytest.fixture
def skin(mesh):
    return make_mesh_skin(mesh)
