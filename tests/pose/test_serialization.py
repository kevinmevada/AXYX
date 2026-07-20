"""Serialization tests."""

from __future__ import annotations

import json

from motion_engine.rendering.avatar.pose import (
    export_debug_report,
    export_hierarchy,
    export_json,
    export_matrices,
)


def test_exports(bind_pose) -> None:
    assert "root" in export_debug_report(bind_pose)
    h = export_hierarchy(bind_pose)
    assert h["roots"] == [0]
    mats = export_matrices(bind_pose)
    assert len(mats["bones"]) == bind_pose.bone_count
    data = json.loads(export_json(bind_pose))
    assert data["kind"] == "bind"
    assert data["bone_count"] == bind_pose.bone_count
