"""Inverse-bind matrix helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from motion_engine.rendering.avatar.pose.matrix_utils import identity_matrix, invert_affine, is_singular
from motion_engine.rendering.avatar.pose.types import Mat4


@dataclass(frozen=True, slots=True)
class BindMatrixSet:
    """Aligned rest-world and inverse-bind buffers."""

    rest_world: tuple[Mat4, ...]
    inverse_bind: tuple[Mat4, ...]

    @property
    def bone_count(self) -> int:
        return len(self.rest_world)

    def ibm(self, index: int) -> Mat4:
        return self.inverse_bind[index]

    def rest(self, index: int) -> Mat4:
        return self.rest_world[index]


def compute_inverse_bind(world: Mat4, authored: Mat4 | None = None) -> Mat4:
    """Return authored IBM or ``inv(world)`` when missing."""
    if authored is not None:
        return np.asarray(authored, dtype=np.float64).reshape(4, 4).copy()
    return invert_affine(world)


def build_bind_matrices(
    world_matrices: list[Mat4],
    authored_ibm: list[Mat4 | None] | None = None,
) -> BindMatrixSet:
    """Build IBM set for every bone."""
    n = len(world_matrices)
    ibm_list: list[Mat4] = []
    rest: list[Mat4] = []
    for i in range(n):
        w = np.asarray(world_matrices[i], dtype=np.float64).reshape(4, 4).copy()
        rest.append(w)
        authored = None if authored_ibm is None else authored_ibm[i]
        ibm_list.append(compute_inverse_bind(w, authored))
    return BindMatrixSet(rest_world=tuple(rest), inverse_bind=tuple(ibm_list))


def validate_ibm_against_world(world: Mat4, ibm: Mat4, *, eps: float = 1e-4) -> bool:
    """True if ``ibm @ world ≈ I`` (within tolerance)."""
    if is_singular(world) or is_singular(ibm):
        return False
    product = ibm @ world
    return bool(np.allclose(product, identity_matrix(), atol=eps, rtol=0.0))


__all__ = [
    "BindMatrixSet",
    "compute_inverse_bind",
    "build_bind_matrices",
    "validate_ibm_against_world",
]
