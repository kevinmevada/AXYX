"""Pose factory tests."""

from __future__ import annotations

import pytest

from motion_engine.rendering.avatar.pose import (
    BindPoseFactory,
    PoseCache,
    PoseFactoryError,
    RestPoseKind,
)
from motion_engine.rendering.avatar.skeleton import AvatarSkeleton
from tests.pose.helpers import make_chain_skeleton


def test_from_skeleton(factory: BindPoseFactory, chain_skeleton: AvatarSkeleton) -> None:
    pose = factory.from_skeleton(chain_skeleton, rest_kind=RestPoseKind.IMPORTED)
    assert pose.skeleton_name == "chain"
    assert pose.rest_info.kind is RestPoseKind.IMPORTED
    assert pose.bone_count == chain_skeleton.bone_count


def test_does_not_mutate_skeleton(factory: BindPoseFactory, chain_skeleton: AvatarSkeleton) -> None:
    name = chain_skeleton.bones[0].name
    factory.from_skeleton(chain_skeleton)
    assert chain_skeleton.bones[0].name == name


def test_empty_raises(factory: BindPoseFactory) -> None:
    class _Empty:
        bone_count = 0
        bones = ()
        name = "e"

    with pytest.raises(PoseFactoryError):
        factory.from_skeleton(_Empty())  # type: ignore[arg-type]


def test_cache_hit(chain_skeleton: AvatarSkeleton) -> None:
    cache = PoseCache()
    fac = BindPoseFactory(cache=cache)
    a = fac.from_skeleton(chain_skeleton, cache_key="k1")
    b = fac.from_skeleton(chain_skeleton, cache_key="k1")
    assert a is b
    assert cache.hits == 1


def test_identity_bind(factory: BindPoseFactory) -> None:
    pose = factory.identity_bind(["r", "a", "b"])
    assert pose.bone_count == 3
    assert pose.find("b").parent_index == 1


def test_t_pose_kind_tag(factory: BindPoseFactory, chain_skeleton: AvatarSkeleton) -> None:
    pose = factory.from_skeleton(chain_skeleton, rest_kind=RestPoseKind.T_POSE)
    assert pose.rest_info.kind is RestPoseKind.T_POSE
