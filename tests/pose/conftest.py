"""Fixtures for M3 pose tests."""

from __future__ import annotations

import pytest

from motion_engine.rendering.avatar.pose import BindPose, BindPoseFactory
from motion_engine.rendering.avatar.skeleton import AvatarSkeleton
from tests.pose.helpers import make_bind_pose, make_chain_skeleton, make_tree_skeleton


@pytest.fixture
def chain_skeleton() -> AvatarSkeleton:
    return make_chain_skeleton(5)


@pytest.fixture
def tree_skeleton() -> AvatarSkeleton:
    return make_tree_skeleton()


@pytest.fixture
def bind_pose(chain_skeleton: AvatarSkeleton) -> BindPose:
    return BindPoseFactory().from_skeleton(chain_skeleton)


@pytest.fixture
def tree_pose(tree_skeleton: AvatarSkeleton) -> BindPose:
    return BindPoseFactory().from_skeleton(tree_skeleton)


@pytest.fixture
def factory() -> BindPoseFactory:
    return BindPoseFactory()
