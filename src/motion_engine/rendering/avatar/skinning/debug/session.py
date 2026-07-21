"""SkinningDebugSession — load avatar + deform for the debug viewer."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from motion_engine.rendering.avatar.models.mesh import MeshData
from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.pose.pose import AnimationPose
from motion_engine.rendering.avatar.skeleton.avatar_skeleton import AvatarSkeleton
from motion_engine.rendering.avatar.skeleton.factory import AvatarSkeletonFactory
from motion_engine.rendering.avatar.skinning.debug.heatmap import weight_heatmap_scalars
from motion_engine.rendering.avatar.skinning.debug.pose_edit import reset_to_bind, rotate_bone
from motion_engine.rendering.avatar.skinning.factory import MeshSkinFactory
from motion_engine.rendering.avatar.skinning.mesh_deformer import DeformedMesh
from motion_engine.rendering.avatar.skinning.mesh_skin import MeshSkin
from motion_engine.rendering.avatar.skinning.skinning_runtime import SkinningRuntime


@dataclass
class SkinningDebugSession:
    """Stateful session for interactive M4 visual validation."""

    mesh: MeshData
    skin: MeshSkin
    skeleton: AvatarSkeleton
    bind: BindPose
    pose: AnimationPose
    runtime: SkinningRuntime = field(default_factory=SkinningRuntime)
    last_deformed: DeformedMesh | None = None
    selected_bone: str = ""
    show_heatmap: bool = False
    rot_x: float = 0.0
    rot_y: float = 0.0
    rot_z: float = 0.0

    @classmethod
    def from_loaded(
        cls,
        mesh: MeshData,
        skeleton: AvatarSkeleton,
        *,
        bind: BindPose | None = None,
    ) -> SkinningDebugSession:
        from motion_engine.rendering.avatar.pose.pose_factory import BindPoseFactory

        skin = MeshSkinFactory().from_mesh(
            mesh,
            bone_count=skeleton.bone_count,
            bone_names=[b.name for b in skeleton.bones],
            skeleton_name=skeleton.name,
        )
        bind_pose = bind or BindPoseFactory().from_skeleton(skeleton)
        pose = reset_to_bind(bind_pose)
        selected = skeleton.bones[0].name if skeleton.bones else ""
        return cls(
            mesh=mesh,
            skin=skin,
            skeleton=skeleton,
            bind=bind_pose,
            pose=pose,
            selected_bone=selected,
        )

    @classmethod
    def load_metahuman(cls, *, lod: int = 3) -> SkinningDebugSession:
        """Load local MetaHuman pack (requires ``assets/avatars/metahuman``)."""
        from motion_engine.rendering.avatar.loader.avatar_loader import AvatarLoader
        from motion_engine.rendering.avatar.pose.pose_factory import BindPoseFactory

        loaded = AvatarLoader().load("avatar.metahuman.default", lod=lod)
        if loaded.skeleton is None or loaded.primary_mesh is None:
            raise RuntimeError("MetaHuman pack missing mesh/skeleton")
        # Convert M1 DTO → M2 runtime skeleton
        runtime_skel = AvatarSkeletonFactory().from_imported(loaded.skeleton)
        bind = BindPoseFactory().from_skeleton(runtime_skel)
        return cls.from_loaded(loaded.primary_mesh, runtime_skel, bind=bind)

    @classmethod
    def load_segment_fixture(cls) -> SkinningDebugSession:
        """Synthetic two-bone segment (always available for CI / offline)."""
        from motion_engine.rendering.avatar.pose.pose_factory import BindPoseFactory
        from tests.skinning.helpers import make_segment_mesh, make_two_bone_skeleton

        mesh = make_segment_mesh(16)
        skel = make_two_bone_skeleton()
        bind = BindPoseFactory().from_skeleton(skel)
        return cls.from_loaded(mesh, skel, bind=bind)

    @classmethod
    def load_fbx(cls, path: str | Path) -> SkinningDebugSession:
        """Load a skinned FBX (requires ``ufbx``)."""
        from experiments.skinning_debug.fbx_import import load_skinned_fbx
        from motion_engine.rendering.avatar.pose.pose_factory import BindPoseFactory
        from motion_engine.rendering.avatar.skeleton.factory import AvatarSkeletonFactory

        mesh, imported = load_skinned_fbx(path)
        runtime_skel = AvatarSkeletonFactory().from_imported(imported)
        bind = BindPoseFactory().from_skeleton(runtime_skel)
        return cls.from_loaded(mesh, runtime_skel, bind=bind)

    @property
    def bone_names(self) -> list[str]:
        return [b.name for b in self.skeleton.bones]

    @property
    def diagnostics(self) -> dict[str, Any]:
        st = self.runtime.last_statistics
        return {
            "vertices": self.mesh.vertex_count,
            "triangles": self.mesh.triangle_count,
            "bones": self.skeleton.bone_count,
            "influences": self.skin.max_influences,
            "skinning_ms": st.skinning_ms if st else 0.0,
            "algorithm": "LBS",
            "backend": "CPU",
            "selected_bone": self.selected_bone,
        }

    def reset(self) -> DeformedMesh:
        self.pose = reset_to_bind(self.bind)
        self.rot_x = self.rot_y = self.rot_z = 0.0
        return self.deform()

    def set_bone_euler(self, bone: str, *, x: float, y: float, z: float) -> DeformedMesh:
        """Reset bone to bind locals then apply XYZ Euler (degrees) and deform."""
        self.selected_bone = bone
        self.rot_x, self.rot_y, self.rot_z = float(x), float(y), float(z)
        pose = reset_to_bind(self.bind)
        if abs(x) > 1e-9:
            pose = rotate_bone(pose, bone, axis="x", angle=x)
        if abs(y) > 1e-9:
            pose = rotate_bone(pose, bone, axis="y", angle=y)
        if abs(z) > 1e-9:
            pose = rotate_bone(pose, bone, axis="z", angle=z)
        self.pose = pose
        return self.deform()

    def deform(self) -> DeformedMesh:
        self.last_deformed = self.runtime.deform(
            self.mesh, self.skin, bind_pose=self.bind, pose=self.pose
        )
        return self.last_deformed

    def heatmap_scalars(self) -> np.ndarray | None:
        if not self.show_heatmap or not self.selected_bone:
            return None
        bi = self.skeleton.index_of(self.selected_bone)
        return weight_heatmap_scalars(self.skin, bi)

    def skeleton_segments(self) -> np.ndarray:
        """Return ``(N, 2, 3)`` line segments parent→child in current pose."""
        segs: list[np.ndarray] = []
        for b in self.pose.bones:
            if b.parent_index is None:
                continue
            p = np.asarray(self.pose.bones[b.parent_index].world_position, dtype=np.float64)
            c = np.asarray(b.world_position, dtype=np.float64)
            segs.append(np.stack([p, c], axis=0))
        if not segs:
            return np.zeros((0, 2, 3), dtype=np.float64)
        return np.stack(segs, axis=0)

    def skeleton_joint_positions(self) -> np.ndarray:
        """Joint markers for bones that participate in the drawn hierarchy.

        Skinning palettes often include hundreds of corrective joints with no
        parent links; plotting all of them clutters the overlay. Prefer
        endpoints of parent→child segments (plus isolated roots of that tree).
        """
        indices: set[int] = set()
        for b in self.pose.bones:
            if b.parent_index is None:
                continue
            indices.add(int(b.index))
            indices.add(int(b.parent_index))
        if not indices:
            # Fallback: show every bone (fixture / fully-rooted skeletons).
            pts = [b.world_position for b in self.pose.bones]
        else:
            pts = [self.pose.bones[i].world_position for i in sorted(indices)]
        if not pts:
            return np.zeros((0, 3), dtype=np.float64)
        return np.asarray(pts, dtype=np.float64)


__all__ = ["SkinningDebugSession"]
