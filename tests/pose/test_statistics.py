"""Statistics tests."""

from __future__ import annotations


def test_statistics(bind_pose) -> None:
    st = bind_pose.statistics
    assert st.bone_count == 5
    assert st.root_count == 1
    assert st.leaf_count == 1
    assert st.hierarchy_depth == 4
    assert st.to_dict()["bone_count"] == 5
