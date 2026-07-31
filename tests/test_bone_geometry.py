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


def test_profile_varies_by_bone_type() -> None:
    femur = profile_for_bone("LFemur")
    hand = profile_for_bone("LHand")
    skull = profile_for_bone("Skull")
    assert femur.shaft_radius > hand.shaft_radius
    assert femur.epiphysis_boost > 0.0
    assert skull.shaft_radius < femur.shaft_radius
    # Side prefix stripping: L/R share the same profile.
    assert profile_for_bone("LFemur") is profile_for_bone("RFemur")
    # Specific rule wins over looser matches.
    assert profile_for_bone("LPelvisHip").shaft_radius == profile_for_bone(
        "RPelvisHip"
    ).shaft_radius


def test_epiphysis_flares_at_ends() -> None:
    profile = profile_for_bone("LFemur")
    mid = radius_at(profile, 0.5)
    assert radius_at(profile, 0.02) > mid
    assert radius_at(profile, 0.98) > mid


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


def test_unknown_bone_falls_back_to_uniform() -> None:
    unknown = profile_for_bone("MysterySegment")
    assert unknown.epiphysis_boost == 0.0
    assert unknown.shaft_radius == 0.55
    assert unknown.min_radius == 9.0


def test_world_radius_respects_category_floors() -> None:
    femur = profile_for_bone("LFemur")
    hand = profile_for_bone("LHand")
    # Small joints still hit the absolute floor (chunky, not wire).
    assert femur.world_radius(10.0) == 16.0
    assert hand.world_radius(10.0) == 7.0
    # Large joints preserve taper hierarchy via ratio.
    assert femur.world_radius(30.0) == 30.0 * 0.85
    assert hand.world_radius(30.0) == 30.0 * 0.45
    assert femur.world_radius(30.0) > hand.world_radius(30.0)
