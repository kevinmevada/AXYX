"""Serialization tests."""

from __future__ import annotations

import json

from motion_engine.rendering.avatar.skinning import (
    export_json,
    export_matrix_palette,
    export_mesh_skin,
    export_weight_table,
    build_matrix_palette,
)


def test_exports(skin, bind) -> None:
    w = export_weight_table(skin.weight_table)
    assert w["vertex_count"] == skin.vertex_count
    pal = build_matrix_palette(bind)
    m = export_matrix_palette(pal)
    assert m["bone_count"] == 2
    raw = export_json(export_mesh_skin(skin))
    assert json.loads(raw)["weights"]["vertex_count"] == skin.vertex_count
