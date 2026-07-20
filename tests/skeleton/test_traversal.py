"""Traversal determinism tests."""

from __future__ import annotations


def test_dfs_preorder(tree_runtime) -> None:
    order = list(tree_runtime.traversal.dfs())
    assert order[0] == 0
    # children of root visited in ascending index: left(1) before right(2)
    assert order.index(1) < order.index(2)
    assert order.index(2) < order.index(3)


def test_dfs_postorder(tree_runtime) -> None:
    order = list(tree_runtime.traversal.dfs_post())
    assert order[-1] == 0
    assert order.index(3) < order.index(2)


def test_bfs(tree_runtime) -> None:
    order = list(tree_runtime.traversal.bfs())
    assert order == [0, 1, 2, 3]


def test_leaves(tree_runtime) -> None:
    leaves = list(tree_runtime.traversal.leaves())
    assert set(leaves) == {1, 3}


def test_root_to_leaf_paths(tree_runtime) -> None:
    paths = list(tree_runtime.traversal.root_to_leaf())
    assert (0, 1) in paths
    assert (0, 2, 3) in paths
    assert len(paths) == 2


def test_topo_parent_before_child(tree_runtime) -> None:
    order = list(tree_runtime.traversal.topo())
    for b in tree_runtime:
        if b.parent_index is not None:
            assert order.index(b.parent_index) < order.index(b.index)


def test_deterministic_repeat(tree_runtime) -> None:
    a = list(tree_runtime.traversal.dfs())
    b = list(tree_runtime.traversal.dfs())
    assert a == b
