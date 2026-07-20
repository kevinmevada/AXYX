"""Serialization tests."""

from __future__ import annotations

import json

from motion_engine.rendering.avatar.skeleton import (
    export_debug,
    export_hierarchy,
    export_json,
    export_metadata,
    export_statistics,
    export_tree,
)


def test_export_tree(tree_runtime) -> None:
    text = export_tree(tree_runtime)
    assert "root" in text
    assert "right_leaf" in text


def test_export_json_roundtrip_parse(tree_runtime) -> None:
    raw = export_json(tree_runtime)
    data = json.loads(raw)
    assert data["statistics"]["bone_count"] == 4
    assert "hierarchy" in data
    assert len(data["bones"]) == 4


def test_export_pieces(tree_runtime) -> None:
    assert export_metadata(tree_runtime)["runtime_version"]
    assert export_statistics(tree_runtime)["leaf_count"] == 2
    h = export_hierarchy(tree_runtime)
    assert h["roots"] == [0]
    dbg = export_debug(tree_runtime)
    assert dbg["name"] == "tree"
