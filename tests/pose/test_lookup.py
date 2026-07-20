"""Lookup API tests."""

from __future__ import annotations

import pytest

from motion_engine.rendering.avatar.pose import PoseBoneNotFoundError


def test_find_and_exists(bind_pose) -> None:
    assert bind_pose.find("b2").index == 2
    assert bind_pose.find(2).name == "b2"
    assert bind_pose.exists("root")
    assert not bind_pose.exists("ghost")


def test_parent_children(bind_pose) -> None:
    assert bind_pose.parent("root") is None
    kids = bind_pose.children("root")
    assert len(kids) == 1
    assert kids[0].name == "b1"


def test_accessors(bind_pose) -> None:
    assert bind_pose.translation("b1")[0] == pytest.approx(1.0, abs=1e-6)
    assert len(bind_pose.rotation("root")) == 4
    assert bind_pose.scale("root") == (1.0, 1.0, 1.0)
    assert bind_pose.world_transform("root").shape == (4, 4)
    assert bind_pose.local_transform("root").shape == (4, 4)
    assert bind_pose.inverse_bind("root").shape == (4, 4)
    assert bind_pose.rest_transform("root").shape == (4, 4)


def test_not_found(bind_pose) -> None:
    with pytest.raises(PoseBoneNotFoundError):
        bind_pose.find("nope")
