"""Regression: M1/M2 freeze, architecture boundaries."""

from __future__ import annotations

import ast
from pathlib import Path

from motion_engine.rendering.avatar import bind_pose as legacy_bind
from motion_engine.rendering.avatar.pose import BindPose as RuntimeBindPose
from motion_engine.rendering.avatar.pose import BindPoseFactory
from motion_engine.rendering.avatar.skeleton import AvatarSkeleton
from tests.pose.helpers import make_chain_skeleton

REPO = Path(__file__).resolve().parents[2]
POSE_PKG = REPO / "src" / "motion_engine" / "rendering" / "avatar" / "pose"
SKELETON_PKG = REPO / "src" / "motion_engine" / "rendering" / "avatar" / "skeleton"


def test_legacy_bind_pose_unchanged() -> None:
    """avatar.bind_pose.BindPose stub remains (M1-era export)."""
    assert legacy_bind.BindPose is not RuntimeBindPose
    bp = legacy_bind.BindPose.from_mapping({"a": (0, 1, 0)})
    assert bp.get("a") is not None


def test_skeleton_api_untouched(chain_skeleton: AvatarSkeleton) -> None:
    assert hasattr(chain_skeleton, "find")
    assert hasattr(chain_skeleton, "rebuild_world_rest")
    BindPoseFactory().from_skeleton(chain_skeleton)
    # still usable after factory
    assert chain_skeleton.find("root").name == "root"


def test_pose_package_no_studio_viewer() -> None:
    forbidden = ("motion_engine.studio", "motion_engine.viewer", "PySide6")
    violations: list[str] = []
    for path in POSE_PKG.rglob("*.py"):
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


def test_skeleton_does_not_import_pose() -> None:
    for path in SKELETON_PKG.rglob("*.py"):
        src = path.read_text(encoding="utf-8")
        assert "rendering.avatar.pose" not in src
