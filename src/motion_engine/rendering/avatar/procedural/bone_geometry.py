"""
Procedural anatomical bone meshes (canonical home under rendering.avatar.procedural).

Each bone is a cortical shaft with epiphyseal flares (femur, tibia, humerus, …)
— not a cylinder / tube. Templates are built once per profile and rigidly
transformed each animation frame (no per-frame mesh regeneration).

World thickness is ``max(base_joint_radius * shaft_ratio, min_radius)`` so the
figure stays solid while femur remains visibly thicker than a finger bone.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final, Sequence

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.floating]


@dataclass(frozen=True, slots=True)
class BoneProfile:
    """Cortical cross-section: world scale + normalized epiphyseal shape.

    ``shaft_ratio`` / ``min_radius`` set world midshaft thickness from the
    average joint radius. The unit template is midshaft=1 so epiphyseal
    flare is shape-only; ``transform_bone`` applies the world radial scale.
    """

    shaft_ratio: float
    min_radius: float
    epiphysis_boost: float
    epiphysis_sigma: float
    axial_slices: int = 10
    radial_sides: int = 14

    @property
    def shaft_radius(self) -> float:
        """Alias for :attr:`shaft_ratio` (legacy call sites / tests)."""
        return self.shaft_ratio

    def world_radius(self, base_joint_radius: float) -> float:
        """World midshaft radius from joint size — never below ``min_radius``."""
        return max(float(base_joint_radius) * self.shaft_ratio, self.min_radius)


# Category table — chunky absolute floors, taper hierarchy preserved.
_PROFILES: Final[dict[str, BoneProfile]] = {
    # Femur / pelvis-hip — thickest load-bearing
    "pelvis_hip": BoneProfile(0.85, 16.0, 0.35, 0.18, axial_slices=8, radial_sides=14),
    "femur": BoneProfile(0.85, 16.0, 0.45, 0.14, axial_slices=10, radial_sides=14),
    # Spine / tibia
    "spine": BoneProfile(0.65, 13.0, 0.25, 0.16, axial_slices=8, radial_sides=14),
    "tibia": BoneProfile(0.65, 13.0, 0.35, 0.14, axial_slices=10, radial_sides=14),
    # Humerus
    "humerus": BoneProfile(0.60, 11.0, 0.35, 0.15, axial_slices=8, radial_sides=12),
    # Forearm / cervical
    "forearm": BoneProfile(0.55, 9.0, 0.30, 0.15, axial_slices=8, radial_sides=12),
    "cervical": BoneProfile(0.55, 9.0, 0.25, 0.18, axial_slices=6, radial_sides=12),
    "uniform": BoneProfile(0.55, 9.0, 0.0, 0.12, axial_slices=8, radial_sides=12),
    # Clavicle / foot / skull
    "clavicle": BoneProfile(0.50, 8.0, 0.20, 0.20, axial_slices=6, radial_sides=10),
    "foot": BoneProfile(0.50, 8.0, 0.20, 0.16, axial_slices=6, radial_sides=10),
    "skull": BoneProfile(0.50, 8.0, 0.15, 0.20, axial_slices=6, radial_sides=10),
    # Hand / toe
    "hand": BoneProfile(0.45, 7.0, 0.15, 0.20, axial_slices=6, radial_sides=10),
    "toe": BoneProfile(0.45, 7.0, 0.15, 0.20, axial_slices=6, radial_sides=10),
}

_UNIFORM_PROFILE: Final[BoneProfile] = _PROFILES["uniform"]

# Ordered (substring, profile_key) rules. Matched against the bone name with
# any leading L/R side prefix stripped, longest/most-specific first so e.g.
# "PelvisHip" doesn't get shadowed by a looser "Pelvis" rule.
_BONE_NAME_RULES: Final[tuple[tuple[str, str], ...]] = (
    ("PelvisHip", "pelvis_hip"),
    ("Femur", "femur"),
    ("Tibia", "tibia"),
    ("Toe", "toe"),
    ("Foot", "foot"),
    ("Clavicle", "clavicle"),
    ("Humerus", "humerus"),
    ("Forearm", "forearm"),
    ("Hand", "hand"),
    ("Cervical", "cervical"),
    ("Skull", "skull"),
    ("Spine", "spine"),
)

_TEMPLATE_CACHE: dict[str, tuple[FloatArray, np.ndarray]] = {}


def profile_for_bone(bone_name: str) -> BoneProfile:
    """Look up the cortical cross-section for a bone by anatomical type.

    Bone names follow the ``[L|R]<Type>`` convention from
    ``skeleton_definition.yaml`` (e.g. ``LFemur``, ``RClavicle``,
    ``Spine``). The side prefix is stripped, then matched against known
    bone-type substrings so every bone gets its own thickness and
    epiphyseal taper instead of one world-constant cylinder. Unrecognized
    names fall back to the flat uniform profile rather than erroring.
    """
    name = bone_name.removeprefix("bone:")
    if name[:1] in ("L", "R") and len(name) > 1 and name[1:2].isupper():
        name = name[1:]
    for substring, profile_key in _BONE_NAME_RULES:
        if substring in name:
            return _PROFILES[profile_key]
    return _UNIFORM_PROFILE


def radius_at(profile: BoneProfile, t: float) -> float:
    """Unit midshaft (=1) with smooth epiphyseal bulges at t≈0 and t≈1."""
    t = float(np.clip(t, 0.0, 1.0))
    sigma = max(profile.epiphysis_sigma, 1e-3)
    proximal = math.exp(-((t / sigma) ** 2))
    distal = math.exp(-(((1.0 - t) / sigma) ** 2))
    return 1.0 * (1.0 + profile.epiphysis_boost * (proximal + distal))


def build_unit_bone_template(profile: BoneProfile) -> tuple[FloatArray, np.ndarray]:
    """Return (vertices, faces) for a unit-length bone along local +Z."""
    cache_key = (
        "unit_v2",
        profile.epiphysis_boost,
        profile.epiphysis_sigma,
        profile.axial_slices,
        profile.radial_sides,
    )
    cached = _TEMPLATE_CACHE.get(str(cache_key))
    if cached is not None:
        return cached[0].copy(), cached[1].copy()

    rings = profile.axial_slices + 1
    sides = profile.radial_sides
    vertices: list[tuple[float, float, float]] = []
    for ring in range(rings):
        t = ring / profile.axial_slices
        z = t
        r = radius_at(profile, t)
        for side in range(sides):
            theta = (2.0 * math.pi * side) / sides
            vertices.append((r * math.cos(theta), r * math.sin(theta), z))

    faces: list[tuple[int, int, int]] = []
    for ring in range(profile.axial_slices):
        row = ring * sides
        next_row = (ring + 1) * sides
        for side in range(sides):
            a = row + side
            b = row + ((side + 1) % sides)
            c = next_row + side
            d = next_row + ((side + 1) % sides)
            faces.append((a, c, b))
            faces.append((b, c, d))

    # Cap proximal end (slightly rounded epiphysis)
    center_top = len(vertices)
    vertices.append((0.0, 0.0, 0.0))
    for side in range(sides):
        faces.append((center_top, side, (side + 1) % sides))

    center_bottom = len(vertices)
    vertices.append((0.0, 0.0, 1.0))
    base = profile.axial_slices * sides
    for side in range(sides):
        faces.append((center_bottom, base + ((side + 1) % sides), base + side))

    pts = np.asarray(vertices, dtype=float)
    tri = np.asarray(faces, dtype=np.int64)
    _TEMPLATE_CACHE[str(cache_key)] = (pts.copy(), tri.copy())
    return pts, tri


def _orthonormal_basis(direction: FloatArray) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Build a stable right-handed basis with +Z aligned to ``direction``."""
    forward = np.asarray(direction, dtype=float)
    length = float(np.linalg.norm(forward))
    if length < 1e-9:
        forward = np.array([0.0, 0.0, 1.0], dtype=float)
        length = 1.0
    z_axis = forward / length
    up = np.array([0.0, 0.0, 1.0], dtype=float)
    if abs(float(np.dot(z_axis, up))) > 0.95:
        up = np.array([0.0, 1.0, 0.0], dtype=float)
    x_axis = np.cross(up, z_axis)
    x_norm = float(np.linalg.norm(x_axis))
    if x_norm < 1e-12:
        x_axis = np.array([1.0, 0.0, 0.0], dtype=float)
    else:
        x_axis = x_axis / x_norm
    y_axis = np.cross(z_axis, x_axis)
    return x_axis, y_axis, z_axis


def transform_bone(
    template: FloatArray,
    start: FloatArray,
    end: FloatArray,
    *,
    radial_scale: float,
    min_length: float = 1.0,
) -> FloatArray:
    """Rigidly place a unit template between ``start`` and ``end``.

    ``radial_scale`` is the world midshaft radius. Only the bone axis is
    stretched to joint distance — cross-section does not grow on long bones.
    """
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    delta = end - start
    length = float(max(np.linalg.norm(delta), min_length))
    x_axis, y_axis, z_axis = _orthonormal_basis(delta)
    rot = np.column_stack((x_axis, y_axis, z_axis))
    scaled = template.copy()
    scaled[:, 0] *= radial_scale
    scaled[:, 1] *= radial_scale
    scaled[:, 2] *= length
    return start + scaled @ rot.T


def merge_bone_meshes(
    parts: Sequence[tuple[FloatArray, np.ndarray]],
) -> tuple[FloatArray, np.ndarray]:
    """Merge placed bone parts into one indexed triangle mesh."""
    if not parts:
        return np.zeros((0, 3), dtype=float), np.zeros((0, 3), dtype=np.int64)
    all_pts: list[FloatArray] = []
    all_faces: list[np.ndarray] = []
    offset = 0
    for pts, faces in parts:
        all_pts.append(pts)
        all_faces.append(faces + offset)
        offset += int(pts.shape[0])
    return np.vstack(all_pts), np.vstack(all_faces)


__all__ = [
    "BoneProfile",
    "build_unit_bone_template",
    "merge_bone_meshes",
    "profile_for_bone",
    "radius_at",
    "transform_bone",
]
