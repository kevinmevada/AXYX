"""Shared helpers for M4 skinning tests."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.models.mesh import MeshData, compute_bounds
from motion_engine.rendering.avatar.models.skeleton import AvatarSkeleton as ImportedSkeleton
from motion_engine.rendering.avatar.models.skeleton import BoneData
from motion_engine.rendering.avatar.pose import BindPose, BindPoseFactory, AnimationPose
from motion_engine.rendering.avatar.skeleton import AvatarSkeletonFactory
from motion_engine.rendering.avatar.skinning import (
    MeshSkin,
    MeshSkinFactory,
    SkinningRuntime,
    WeightTable,
)


def make_two_bone_skeleton():
    def W(x: float):
        m = np.eye(4)
        m[0, 3] = x
        return m

    imp = ImportedSkeleton(
        name="arm",
        bones=(
            BoneData(0, "root", None, (0, 0, 0), W(0), np.linalg.inv(W(0))),
            BoneData(1, "forearm", 0, (1, 0, 0), W(1), np.linalg.inv(W(1))),
        ),
    )
    return AvatarSkeletonFactory().from_imported(imp)


def make_bind() -> BindPose:
    return BindPoseFactory().from_skeleton(make_two_bone_skeleton())


def make_segment_mesh(n: int = 5) -> MeshData:
    """Vertices along +X from 0..2; root↔forearm blend by position.

    Forearm bind origin is at x=1, so the tip (x=2) lies in the forearm
    bone's rest space and moves under forearm rotation.
    """
    xs = np.linspace(0.0, 2.0, n, dtype=np.float32)
    pos = np.stack([xs, np.zeros(n, np.float32), np.zeros(n, np.float32)], axis=1)
    nrm = np.tile(np.array([[0, 1, 0]], dtype=np.float32), (n, 1))
    uvs = np.stack([xs / 2.0, np.zeros(n, np.float32)], axis=1)
    if n >= 3:
        indices = []
        for i in range(n - 2):
            indices.extend([i, i + 1, i + 2])
        idx = np.asarray(indices, dtype=np.int32)
    else:
        idx = np.array([0, 1, 0], dtype=np.int32)
    # blend: weight_forearm = clamp(x, 0, 1) for x in [0,1], then 1 for x>1
    w_fore = np.clip(xs, 0.0, 1.0)
    j_idx = np.full((n, 4), -1, dtype=np.int32)
    j_w = np.zeros((n, 4), dtype=np.float32)
    j_idx[:, 0] = 0
    j_idx[:, 1] = 1
    j_w[:, 1] = w_fore
    j_w[:, 0] = 1.0 - w_fore
    return MeshData(
        name="segment",
        positions=pos,
        normals=nrm,
        uvs=uvs,
        indices=idx,
        bounds=compute_bounds(pos),
        joint_indices=j_idx,
        joint_weights=j_w,
        format="test",
    )


def make_mesh_skin(mesh: MeshData | None = None) -> MeshSkin:
    mesh = mesh or make_segment_mesh()
    return MeshSkinFactory().from_mesh(mesh, bone_count=2, bone_names=["root", "forearm"])


def rotate_forearm(bind: BindPose, degrees: float = 90.0) -> AnimationPose:
    """Animation pose with forearm local rotation about Z."""
    anim = AnimationPose.from_pose(bind)
    rad = np.deg2rad(degrees)
    c, s = np.cos(rad), np.sin(rad)
    # Rebuild world via set local on forearm then manual FK for test:
    # Use BindPoseFactory-style: mutate by replacing bone with rotated global.
    from motion_engine.rendering.avatar.pose.pose import BonePose
    from motion_engine.rendering.avatar.pose.transform_propagation import (
        propagate_world_transforms,
    )

    locals_m = [b.local_matrix.copy() for b in anim.bones]
    rot = np.eye(4)
    rot[0, 0] = c
    rot[0, 1] = -s
    rot[1, 0] = s
    rot[1, 1] = c
    # forearm local = translation * rotation (keep translation from derived local)
    locals_m[1] = locals_m[1] @ rot
    parents = [b.parent_index for b in anim.bones]
    worlds = list(propagate_world_transforms(locals_m, parents).world_matrices)
    new_bones = []
    for i, b in enumerate(anim.bones):
        new_bones.append(
            BonePose.from_matrices(
                bone_id=b.bone_id,
                index=b.index,
                name=b.name,
                parent_index=b.parent_index,
                children=b.children,
                local_matrix=locals_m[i],
                global_matrix=worlds[i],
                rest_matrix=b.rest_matrix,
                inverse_bind_matrix=b.inverse_bind_matrix,
                metadata=dict(b.metadata),
            )
        )
    return AnimationPose(_name="bent", _bones=new_bones)
