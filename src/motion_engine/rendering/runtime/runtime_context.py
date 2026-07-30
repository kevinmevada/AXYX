"""Prepared runtime context — owns loaded resources for a session."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.pose.pose import AnimationPose
from motion_engine.rendering.avatar.retarget.retarget_context import RetargetContext
from motion_engine.rendering.avatar.retarget.retarget_engine import RetargetEngine
from motion_engine.rendering.avatar.retarget.retarget_session import RetargetSession
from motion_engine.rendering.avatar.retarget.types import MotionPose, MotionSkeleton
from motion_engine.rendering.avatar.skeleton.avatar_skeleton import AvatarSkeleton
from motion_engine.rendering.avatar.skinning.mesh_skin import MeshSkin
from motion_engine.rendering.avatar.models.mesh import MeshData
from motion_engine.rendering.avatar.skinning.skinning_runtime import SkinningRuntime
from motion_engine.rendering.avatar.skinning.mesh_deformer import DeformedMesh
from motion_engine.rendering.runtime.runtime_session import RuntimeSession


@dataclass
class RuntimeContext:
    """Prepared resources for the active research session.

    Does not mutate BindPose / AvatarSkeleton; holds references only.
    """

    session: RuntimeSession
    skeleton: AvatarSkeleton | None = None
    bind: BindPose | None = None
    mesh: MeshData | None = None
    skin: MeshSkin | None = None
    skinning: SkinningRuntime | None = None
    motion_skeleton: MotionSkeleton | None = None
    motion_poses: list[MotionPose] = field(default_factory=list)
    retarget_engine: RetargetEngine | None = None
    retarget_context: RetargetContext | None = None
    retarget_session: RetargetSession | None = None
    last_pose: AnimationPose | None = None
    last_deformed: DeformedMesh | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def clear_outputs(self) -> None:
        self.last_pose = None
        self.last_deformed = None


__all__ = ["RuntimeContext"]
