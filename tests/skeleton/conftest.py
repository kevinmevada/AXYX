"""Shared fixtures for M2 skeleton unit tests."""

from __future__ import annotations

import pytest

from motion_engine.rendering.avatar.skeleton import AvatarSkeleton, AvatarSkeletonFactory
from tests.skeleton.helpers import make_chain_imported, make_tree_imported


@pytest.fixture
def chain_runtime() -> AvatarSkeleton:
    return AvatarSkeletonFactory().from_imported(make_chain_imported(5))


@pytest.fixture
def tree_runtime() -> AvatarSkeleton:
    return AvatarSkeletonFactory().from_imported(make_tree_imported())


@pytest.fixture
def factory() -> AvatarSkeletonFactory:
    return AvatarSkeletonFactory()
