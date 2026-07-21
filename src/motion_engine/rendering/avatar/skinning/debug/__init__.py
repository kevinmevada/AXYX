"""Non-exported skinning debug utilities (M4 visual validation).

Not part of the frozen public ``skinning`` API — import from this subpackage
directly for experiments and visual tests.
"""

from __future__ import annotations

from motion_engine.rendering.avatar.skinning.debug.bone_sweep import (
    BoneSweepReport,
    sweep_all_bones,
    sweep_bone,
    validate_deformed_mesh,
)
from motion_engine.rendering.avatar.skinning.debug.heatmap import (
    weight_heatmap_scalars,
    weight_heatmap_rgb,
)
from motion_engine.rendering.avatar.skinning.debug.pose_edit import (
    rebuild_animation_fk,
    reset_to_bind,
    rotate_bone,
)
from motion_engine.rendering.avatar.skinning.debug.session import SkinningDebugSession

__all__ = [
    "BoneSweepReport",
    "SkinningDebugSession",
    "rebuild_animation_fk",
    "reset_to_bind",
    "rotate_bone",
    "sweep_all_bones",
    "sweep_bone",
    "validate_deformed_mesh",
    "weight_heatmap_rgb",
    "weight_heatmap_scalars",
]
