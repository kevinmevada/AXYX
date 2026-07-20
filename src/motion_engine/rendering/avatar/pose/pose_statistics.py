"""Automatic pose statistics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence

from motion_engine.rendering.avatar.pose.pose import BonePose


@dataclass(frozen=True, slots=True)
class PoseStatistics:
    """Computed pose / propagation statistics."""

    bone_count: int
    root_count: int
    leaf_count: int
    hierarchy_depth: int
    transform_count: int
    matrix_inversion_count: int
    propagation_depth: int
    average_children: float
    bones_with_ibm: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_pose_statistics(
    bones: Sequence[BonePose],
    parents: list[int | None],
    *,
    matrix_inversion_count: int | None = None,
) -> PoseStatistics:
    """Compute statistics from bone poses."""
    n = len(bones)
    root_count = sum(1 for p in parents if p is None)
    leaf_count = sum(1 for b in bones if not b.children)
    # depth
    depth = [0] * n
    changed = True
    while changed:
        changed = False
        for i, p in enumerate(parents):
            if p is None:
                continue
            nd = depth[p] + 1
            if nd > depth[i]:
                depth[i] = nd
                changed = True
    hier_depth = max(depth) if depth else 0
    branch = [len(b.children) for b in bones if b.children]
    avg = (sum(branch) / len(branch)) if branch else 0.0
    ibm_n = sum(1 for b in bones if b.inverse_bind_matrix is not None)
    inv_count = matrix_inversion_count if matrix_inversion_count is not None else n
    return PoseStatistics(
        bone_count=n,
        root_count=root_count,
        leaf_count=leaf_count,
        hierarchy_depth=hier_depth,
        transform_count=n * 3,  # local + global + rest
        matrix_inversion_count=inv_count,
        propagation_depth=hier_depth,
        average_children=avg,
        bones_with_ibm=ibm_n,
    )


__all__ = ["PoseStatistics", "compute_pose_statistics"]
