"""Tests for anatomical bone transforms and mapping."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml

from motion_engine.rendering.visualization.transforms import bone_user_matrix, euler_xyz_matrix


def test_bone_user_matrix_places_along_segment() -> None:
    start = np.array([0.0, 0.0, 0.0])
    end = np.array([0.0, 0.0, 400.0])
    mat = bone_user_matrix(start, end, radial_scale=10.0)
    # Origin of mesh (0,0,0) → start
    origin = mat @ np.array([0.0, 0.0, 0.0, 1.0])
    tip = mat @ np.array([0.0, 0.0, 1.0, 1.0])
    assert np.allclose(origin[:3], start, atol=1e-6)
    assert np.allclose(tip[:3], end, atol=1e-6)


def test_euler_identity() -> None:
    m = euler_xyz_matrix((0.0, 0.0, 0.0))
    assert np.allclose(m, np.eye(3))


def test_bone_mapping_yaml_covers_skeleton_bones() -> None:
    root = Path(__file__).resolve().parents[2]
    mapping = yaml.safe_load(
        (root / "config" / "bone_mapping.yaml").read_text(encoding="utf-8")
    )
    skel = yaml.safe_load(
        (root / "config" / "skeleton_definition.yaml").read_text(encoding="utf-8")
    )
    mapped = set(mapping["bones"])
    defined = set(skel["bones"])
    assert mapped == defined
