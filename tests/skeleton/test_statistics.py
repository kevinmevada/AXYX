"""Statistics tests."""

from __future__ import annotations


def test_chain_statistics(chain_runtime) -> None:
    s = chain_runtime.statistics
    assert s.bone_count == 5
    assert s.leaf_count == 1
    assert s.root_count == 1
    assert s.tree_depth == 4
    assert s.longest_chain == 5
    assert s.cycle_count == 0
    assert s.unique_name_count == 5


def test_tree_statistics(tree_runtime) -> None:
    s = tree_runtime.statistics
    assert s.bone_count == 4
    assert s.leaf_count == 2
    assert s.max_branching == 2
    assert s.average_branching_factor > 0
    d = s.to_dict()
    assert d["bone_count"] == 4
