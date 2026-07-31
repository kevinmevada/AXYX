"""Tests for BoneAssetLoader."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from motion_engine.rendering.visualization.bone_asset_loader import BoneAssetLoader
from motion_engine.rendering.visualization.bone_asset_manager import BoneAssetManager


def test_asset_manager_generates_local_pack(tmp_path: Path) -> None:
    mgr = BoneAssetManager(tmp_path / "bones")
    assert not mgr.is_installed()
    assert mgr.ensure_installed()
    assert mgr.is_installed()
    assert (tmp_path / "bones" / "femur.obj").is_file()
    # Second call is a no-op.
    assert mgr.ensure_installed()


def test_loader_discovers_and_caches(tmp_path: Path) -> None:
    pytest.importorskip("pyvista")
    mgr = BoneAssetManager(tmp_path / "bones")
    assert mgr.ensure_installed()
    loader = BoneAssetLoader([tmp_path / "bones"])
    names = loader.discover()
    assert "femur" in names
    mesh = loader.load("femur.obj")
    assert mesh is not None
    assert mesh.n_points > 0
    # Cached identity
    assert loader.load("femur") is mesh


def test_loader_missing_mesh_returns_none(tmp_path: Path) -> None:
    loader = BoneAssetLoader([tmp_path])
    assert loader.load("does_not_exist.obj") is None
