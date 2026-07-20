"""Lookup API tests."""

from __future__ import annotations

import pytest

from motion_engine.rendering.avatar.skeleton import BoneNotFoundError


def test_find_by_name_and_index(chain_runtime) -> None:
    assert chain_runtime.find("root").index == 0
    assert chain_runtime.find(2).name == "b2"
    assert chain_runtime.index_of("b3") == 3


def test_exists(chain_runtime) -> None:
    assert chain_runtime.exists("root")
    assert chain_runtime.exists(4)
    assert not chain_runtime.exists("nope")
    assert not chain_runtime.exists(99)


def test_try_bone(chain_runtime) -> None:
    assert chain_runtime.try_bone("missing") is None
    assert chain_runtime.try_bone("root") is not None


def test_not_found(chain_runtime) -> None:
    with pytest.raises(BoneNotFoundError):
        chain_runtime.find("ghost")


def test_parent_children_root_leaf(chain_runtime) -> None:
    assert chain_runtime.parent("root") is None
    assert chain_runtime.is_root("root")
    kids = chain_runtime.children("root")
    assert len(kids) == 1
    assert kids[0].name == "b1"
    assert chain_runtime.is_leaf("b4")
    assert chain_runtime.root("b4").name == "root"


def test_o1_lookup_consistency(chain_runtime) -> None:
    for b in chain_runtime:
        assert chain_runtime.lookup.by_name[b.name] == b.index
        assert chain_runtime.lookup.by_id[int(b.id)] == b.index
