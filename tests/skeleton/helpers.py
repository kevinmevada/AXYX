"""Helpers shared by M2 skeleton tests (importable without pytest)."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.models.skeleton import AvatarSkeleton as ImportedSkeleton
from motion_engine.rendering.avatar.models.skeleton import BoneData


def make_chain_imported(n: int = 4) -> ImportedSkeleton:
    bones = []
    for i in range(n):
        parent = None if i == 0 else i - 1
        bones.append(
            BoneData(
                index=i,
                name="root" if i == 0 else f"b{i}",
                parent_index=parent,
                local_translation=(float(i), 0.0, 0.0),
                bind_world=np.eye(4),
                inverse_bind=np.eye(4),
            )
        )
    return ImportedSkeleton(name="chain", bones=tuple(bones))


def make_tree_imported() -> ImportedSkeleton:
    eye = np.eye(4)
    bones = (
        BoneData(0, "root", None, (0, 0, 0), eye.copy(), eye.copy()),
        BoneData(1, "left", 0, (1, 0, 0), eye.copy(), eye.copy()),
        BoneData(2, "right", 0, (-1, 0, 0), eye.copy(), eye.copy()),
        BoneData(3, "right_leaf", 2, (0, 1, 0), eye.copy(), eye.copy()),
    )
    return ImportedSkeleton(name="tree", bones=bones)
