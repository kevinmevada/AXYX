"""Helpers for M3 pose tests."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.models.skeleton import AvatarSkeleton as ImportedSkeleton
from motion_engine.rendering.avatar.models.skeleton import BoneData
from motion_engine.rendering.avatar.pose import BindPose, BindPoseFactory
from motion_engine.rendering.avatar.skeleton import AvatarSkeleton, AvatarSkeletonFactory


def make_chain_skeleton(n: int = 4) -> AvatarSkeleton:
    bones = []
    world = np.eye(4)
    for i in range(n):
        parent = None if i == 0 else i - 1
        # accumulate translation along X in bind world
        w = np.eye(4)
        w[0, 3] = float(i)
        bones.append(
            BoneData(
                index=i,
                name="root" if i == 0 else f"b{i}",
                parent_index=parent,
                local_translation=(1.0 if i else 0.0, 0.0, 0.0),
                bind_world=w,
                inverse_bind=np.linalg.inv(w),
            )
        )
    imported = ImportedSkeleton(name="chain", bones=tuple(bones))
    return AvatarSkeletonFactory().from_imported(imported)


def make_tree_skeleton() -> AvatarSkeleton:
    def bone(i: int, name: str, parent: int | None, tx: float, ty: float = 0.0) -> BoneData:
        w = np.eye(4)
        w[0, 3] = tx
        w[1, 3] = ty
        return BoneData(i, name, parent, (tx, ty, 0.0), w, np.linalg.inv(w))

    imported = ImportedSkeleton(
        name="tree",
        bones=(
            bone(0, "root", None, 0.0),
            bone(1, "left", 0, 1.0),
            bone(2, "right", 0, -1.0),
            bone(3, "right_leaf", 2, -1.0, 1.0),
        ),
    )
    return AvatarSkeletonFactory().from_imported(imported)


def make_bind_pose(n: int = 4) -> BindPose:
    return BindPoseFactory().from_skeleton(make_chain_skeleton(n))
