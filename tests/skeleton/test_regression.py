"""Regression: M1 import DTO unchanged; M2 is additive."""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np

from motion_engine.rendering.avatar.models.skeleton import AvatarSkeleton as ImportedSkeleton
from motion_engine.rendering.avatar.models.skeleton import BoneData
from motion_engine.rendering.avatar.skeleton import AvatarSkeleton, AvatarSkeletonFactory


REPO = Path(__file__).resolve().parents[2]
SKELETON_PKG = REPO / "src" / "motion_engine" / "rendering" / "avatar" / "skeleton"


def test_m1_bone_data_fields_stable() -> None:
    fields = {f.name for f in BoneData.__dataclass_fields__.values()}  # type: ignore[attr-defined]
    assert fields >= {
        "index",
        "name",
        "parent_index",
        "local_translation",
        "bind_world",
        "inverse_bind",
    }


def test_runtime_distinct_from_imported() -> None:
    assert ImportedSkeleton is not AvatarSkeleton


def test_factory_does_not_mutate_imported() -> None:
    eye = np.eye(4)
    bones = (BoneData(0, "r", None, (0, 0, 0), eye, eye),)
    imp = ImportedSkeleton(name="x", bones=bones)
    before = imp.bones[0].name
    AvatarSkeletonFactory().from_imported(imp)
    assert imp.bones[0].name == before


def test_skeleton_package_no_studio_viewer_imports() -> None:
    forbidden = ("motion_engine.studio", "motion_engine.viewer", "PySide6")
    violations: list[str] = []
    for path in SKELETON_PKG.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            mods: list[str] = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods = [node.module]
            for m in mods:
                for f in forbidden:
                    if m == f or m.startswith(f + "."):
                        violations.append(f"{path.name}:{m}")
    assert violations == []


def test_no_circular_import_models() -> None:
    """models.skeleton must not import runtime skeleton package."""
    src = (REPO / "src/motion_engine/rendering/avatar/models/skeleton.py").read_text(
        encoding="utf-8"
    )
    assert "rendering.avatar.skeleton" not in src
