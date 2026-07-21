"""Regression: M1–M3 freeze, legacy stub, architecture."""

from __future__ import annotations

import ast
from pathlib import Path

from motion_engine.rendering.avatar.skinning import MeshSkin, SkinningRuntime

REPO = Path(__file__).resolve().parents[2]
PKG = REPO / "src" / "motion_engine" / "rendering" / "avatar" / "skinning"


def test_legacy_stub_untouched() -> None:
    from motion_engine.rendering.avatar.skinning import (
        SkinningWeights,
        apply_linear_blend_skinning,
    )

    assert SkinningWeights is not None
    assert callable(apply_linear_blend_skinning)


def test_no_circular_into_frozen() -> None:
    for pkg in ("skeleton", "pose"):
        root = REPO / "src" / "motion_engine" / "rendering" / "avatar" / pkg
        for path in root.rglob("*.py"):
            assert "rendering.avatar.skinning" not in path.read_text(encoding="utf-8")


def test_layer_isolation() -> None:
    forbidden = ("motion_engine.studio", "motion_engine.viewer", "PySide6")
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
                    assert not (m == f or m.startswith(f + ".")), f"{path}:{m}"
