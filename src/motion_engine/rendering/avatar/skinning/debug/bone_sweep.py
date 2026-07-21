"""Deformed-mesh validation + automated bone angle sweeps."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

import numpy as np

from motion_engine.rendering.avatar.models.mesh import MeshData
from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.pose.pose import AnimationPose
from motion_engine.rendering.avatar.skinning.debug.pose_edit import reset_to_bind, rotate_bone
from motion_engine.rendering.avatar.skinning.mesh_deformer import DeformedMesh
from motion_engine.rendering.avatar.skinning.mesh_skin import MeshSkin
from motion_engine.rendering.avatar.skinning.skinning_runtime import SkinningRuntime


@dataclass(frozen=True, slots=True)
class MeshValidationIssue:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class MeshValidationReport:
    issues: tuple[MeshValidationIssue, ...]

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0


def validate_deformed_mesh(
    source: MeshData,
    deformed: DeformedMesh,
    *,
    max_extent: float = 1e6,
) -> MeshValidationReport:
    """Check finiteness, topology, and non-exploding bounds."""
    issues: list[MeshValidationIssue] = []
    if deformed.vertex_count != source.vertex_count:
        issues.append(
            MeshValidationIssue("VERT_COUNT", "Deformed vertex count != source")
        )
    if not np.array_equal(deformed.indices, source.indices):
        issues.append(MeshValidationIssue("TOPOLOGY", "Index buffer changed"))
    if not np.all(np.isfinite(deformed.positions)):
        issues.append(MeshValidationIssue("NAN_POS", "Non-finite positions"))
    if not np.all(np.isfinite(deformed.normals)):
        issues.append(MeshValidationIssue("NAN_NRM", "Non-finite normals"))
    extent = float(np.max(np.abs(deformed.positions))) if deformed.vertex_count else 0.0
    if extent > max_extent:
        issues.append(
            MeshValidationIssue("EXPLODE", f"Position extent {extent} > {max_extent}")
        )
    return MeshValidationReport(tuple(issues))


@dataclass
class BoneSweepReport:
    bone_name: str
    angles_tested: int = 0
    failures: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures


def sweep_bone(
    *,
    mesh: MeshData,
    skin: MeshSkin,
    bind: BindPose,
    bone_name: str,
    angles: Sequence[float],
    axis: str = "z",
    runtime: SkinningRuntime | None = None,
) -> BoneSweepReport:
    """Rotate one bone through ``angles`` and validate each deformation."""
    rt = runtime or SkinningRuntime()
    report = BoneSweepReport(bone_name=bone_name)
    for angle in angles:
        pose = rotate_bone(reset_to_bind(bind), bone_name, axis=axis, angle=float(angle))
        deformed = rt.deform(mesh, skin, bind_pose=bind, pose=pose)
        vr = validate_deformed_mesh(mesh, deformed)
        report.angles_tested += 1
        if not vr.ok:
            report.failures.append(
                f"angle={angle}: " + "; ".join(i.code for i in vr.issues)
            )
    return report


def sweep_all_bones(
    *,
    mesh: MeshData,
    skin: MeshSkin,
    bind: BindPose,
    angles: Sequence[float] | None = None,
    axis: str = "z",
    bone_names: Iterable[str] | None = None,
    runtime: SkinningRuntime | None = None,
) -> list[BoneSweepReport]:
    """Sweep many bones (default: all pose bones)."""
    angles = list(angles) if angles is not None else list(range(-90, 91, 30))
    names = list(bone_names) if bone_names is not None else [b.name for b in bind.bones]
    return [
        sweep_bone(
            mesh=mesh,
            skin=skin,
            bind=bind,
            bone_name=name,
            angles=angles,
            axis=axis,
            runtime=runtime,
        )
        for name in names
    ]


__all__ = [
    "MeshValidationIssue",
    "MeshValidationReport",
    "BoneSweepReport",
    "validate_deformed_mesh",
    "sweep_bone",
    "sweep_all_bones",
]
