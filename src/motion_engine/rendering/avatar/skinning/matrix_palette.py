"""Skinning matrix palette: current_pose @ inverse_bind."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from motion_engine.rendering.avatar.pose.pose import Pose
from motion_engine.rendering.avatar.skinning.bone_palette import BonePalette
from motion_engine.rendering.avatar.skinning.types import Mat4


@dataclass(frozen=True, slots=True)
class MatrixPalette:
    """Per-bone (or per-palette-slot) 4×4 skinning matrices."""

    matrices: tuple[Mat4, ...]

    def __post_init__(self) -> None:
        mats = tuple(
            np.asarray(m, dtype=np.float64).reshape(4, 4).copy() for m in self.matrices
        )
        object.__setattr__(self, "matrices", mats)

    @property
    def bone_count(self) -> int:
        return len(self.matrices)

    def as_array(self) -> np.ndarray:
        """Stack to ``(B, 4, 4)`` float64."""
        if not self.matrices:
            return np.zeros((0, 4, 4), dtype=np.float64)
        return np.stack(self.matrices, axis=0)


def build_matrix_palette(
    pose: Pose,
    *,
    bone_palette: BonePalette | None = None,
) -> MatrixPalette:
    """Compute skin matrices ``world @ inverse_bind`` for each bone/slot.

    Uses the pose's current global transform and inverse bind matrix.
    """
    if bone_palette is None:
        bone_palette = BonePalette.identity(pose.bone_count, names=[b.name for b in pose.bones])
    mats: list[Mat4] = []
    for skel_idx in bone_palette.bone_indices.tolist():
        bone = pose.bones[int(skel_idx)]
        skin = bone.global_matrix @ bone.inverse_bind_matrix
        mats.append(skin)
    return MatrixPalette(matrices=tuple(mats))


__all__ = ["MatrixPalette", "build_matrix_palette"]
