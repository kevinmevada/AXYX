"""Statistics / serialization / regression tests."""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np

from motion_engine.rendering.avatar.skinning import (
    SkinningRuntime,
    export_debug_report,
    export_mesh_skin,
)
from tests.skinning.helpers import make_bind, make_mesh_skin, make_segment_mesh

REPO = Path(__file__).resolve().parents[2]
PKG = REPO / "src" / "motion_engine" / "rendering" / "avatar" / "skinning"


def test_statistics(mesh, skin, bind) -> None:
    rt = SkinningRuntime()
    rt.deform(mesh, skin, bind_pose=bind)
    assert rt.last_statistics is not None
    assert rt.last_statistics.vertex_count == mesh.vertex_count
    d = rt.last_statistics.to_dict()
    assert "skinning_ms" in d


def test_serialization(skin) -> None:
    data = export_mesh_skin(skin)
    assert data["weights"]["vertex_count"] == skin.vertex_count
    assert "MeshSkin" in export_debug_report(skin)


def test_no_studio_viewer_imports() -> None:
    forbidden = ("motion_engine.studio", "motion_engine.viewer", "PySide6")
    violations = []
    for path in PKG.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods = [node.module]
            for m in mods:
                for f in forbidden:
                    if m == f or m.startswith(f + "."):
                        violations.append(f"{path.name}:{m}")
    assert violations == []


def test_frozen_packages_not_importing_skinning() -> None:
    for pkg in ("skeleton", "pose"):
        root = REPO / "src" / "motion_engine" / "rendering" / "avatar" / pkg
        for path in root.rglob("*.py"):
            assert "rendering.avatar.skinning" not in path.read_text(encoding="utf-8")


def test_legacy_stub_distinct() -> None:
    from motion_engine.rendering.avatar.skinning import MeshSkin, SkinningWeights

    assert SkinningWeights is not None
    assert MeshSkin is not SkinningWeights
