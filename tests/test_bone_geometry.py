"""Tests for procedural anatomical bone meshes."""

from __future__ import annotations

import numpy as np

from motion_engine.bone_geometry import (
    build_unit_bone_template,
    merge_bone_meshes,
    profile_for_bone,
    radius_at,
    transform_bone,
)


def test_profile_is_uniform_for_all_bones() -> None:
    assert profile_for_bone("LFemur") is profile_for_bone("LHand")
    assert profile_for_bone("Skull").epiphysis_boost == 0.0


def test_epiphysis_is_uniform_shaft() -> None:
    profile = profile_for_bone("LFemur")
    assert radius_at(profile, 0.02) == radius_at(profile, 0.5)
    assert radius_at(profile, 0.98) == radius_at(profile, 0.5)


def test_unit_template_has_caps_and_faces() -> None:
    profile = profile_for_bone("RFemur")
    points, faces = build_unit_bone_template(profile)
    expected_verts = (profile.axial_slices + 1) * profile.radial_sides + 2
    assert points.shape == (expected_verts, 3)
    assert faces.ndim == 2
    assert faces.shape[1] == 3
    assert np.isclose(points[:, 2].min(), 0.0)
    assert np.isclose(points[:, 2].max(), 1.0)


def test_transform_places_bone_between_joints() -> None:
    profile = profile_for_bone("LTibia")
    unit, _faces = build_unit_bone_template(profile)
    start = np.array([0.0, 0.0, 0.0], dtype=float)
    end = np.array([0.0, 0.0, 400.0], dtype=float)
    placed = transform_bone(unit, start, end, radial_scale=18.0)
    proximal_cap = (profile.axial_slices + 1) * profile.radial_sides
    distal_cap = proximal_cap + 1
    assert np.linalg.norm(placed[proximal_cap] - start) < 1.0
    assert np.linalg.norm(placed[distal_cap] - end) < 1.0


def test_merge_bone_meshes_offsets_faces() -> None:
    a_pts, a_faces = build_unit_bone_template(profile_for_bone("LFemur"))
    b_pts, b_faces = build_unit_bone_template(profile_for_bone("RFemur"))
    verts, faces = merge_bone_meshes([(a_pts, a_faces), (b_pts, b_faces)])
    assert verts.shape[0] == a_pts.shape[0] + b_pts.shape[0]
    assert faces.shape[0] == a_faces.shape[0] + b_faces.shape[0]
    assert faces.max() == verts.shape[0] - 1
