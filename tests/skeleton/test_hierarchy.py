"""Hierarchy query tests."""

from __future__ import annotations

from motion_engine.rendering.avatar.skeleton.hierarchy import (
    detect_cycle,
    find_roots,
    lowest_common_ancestor,
)


def test_find_roots() -> None:
    assert find_roots([None, 0, 0, 1]) == [0]


def test_detect_cycle_none() -> None:
    assert detect_cycle([None, 0, 1, 2]) == []


def test_detect_cycle_loop() -> None:
    cyc = detect_cycle([1, 2, 0])
    assert cyc
    assert cyc[0] == cyc[-1]


def test_tree_lca(tree_runtime) -> None:
    lca = tree_runtime.common_ancestor("left", "right_leaf")
    assert lca is not None
    assert lca.name == "root"


def test_ancestors_descendants(tree_runtime) -> None:
    assert tree_runtime.ancestors("right_leaf") == (2, 0)
    assert set(tree_runtime.descendants("root")) == {1, 2, 3}
    assert tree_runtime.descendants("left") == ()


def test_siblings(tree_runtime) -> None:
    names = {b.name for b in tree_runtime.siblings("left")}
    assert names == {"right"}


def test_path_and_depth(tree_runtime) -> None:
    assert tree_runtime.path("right_leaf") == "root/right/right_leaf"
    assert tree_runtime.depth("root") == 0
    assert tree_runtime.depth("right_leaf") == 2
    assert tree_runtime.height("right_leaf") == 0
    assert tree_runtime.height("root") == 2


def test_lowest_common_ancestor_fn() -> None:
    parents = [None, 0, 0, 2]
    assert lowest_common_ancestor(1, 3, parents) == 0
