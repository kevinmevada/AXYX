"""Validation — mappings, quaternions, hierarchy, NaN/Inf, limits."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from motion_engine.rendering.avatar.pose.pose import AnimationPose
from motion_engine.rendering.avatar.retarget._quat import q_normalize
from motion_engine.rendering.avatar.retarget.constants import QUAT_NORM_TOL
from motion_engine.rendering.avatar.retarget.types import MappingProfile, MotionPose, MotionSkeleton


@dataclass
class ValidationReport:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def error(self, msg: str) -> None:
        self.ok = False
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "metadata": dict(self.metadata),
        }


class RetargetValidator:
    """Validate profiles, poses, and retarget outputs."""

    def validate_profile(
        self,
        profile: MappingProfile,
        source: MotionSkeleton | None = None,
        target_names: set[str] | None = None,
    ) -> ValidationReport:
        report = ValidationReport()
        if not profile.bones:
            report.error("Mapping profile has no bones")
        seen_src: set[str] = set()
        for e in profile.bones:
            if not e.source:
                report.error("Empty source in bone entry")
            if not e.targets:
                report.error(f"No targets for source {e.source}")
            if e.source in seen_src and e.kind.value == "one_to_one":
                report.warn(f"Duplicate source mapping: {e.source}")
            seen_src.add(e.source)
            for t in e.targets:
                if target_names is not None and t not in target_names and not e.optional:
                    report.warn(f"Target bone not in avatar: {t}")
        if source is not None:
            src_names = set(source.joint_names)
            for e in profile.bones:
                if e.source not in src_names and not e.optional:
                    report.warn(f"Source bone not in motion skeleton: {e.source}")
        return report

    def validate_motion_pose(self, pose: MotionPose) -> ValidationReport:
        report = ValidationReport()
        for name, sample in pose.joints.items():
            q = np.asarray(sample.rotation_xyzw, dtype=np.float64)
            if not np.all(np.isfinite(q)):
                report.error(f"Non-finite quaternion: {name}")
            n = float(np.linalg.norm(q))
            if abs(n - 1.0) > 0.1:
                report.warn(f"Quaternion not unit ({n:.4f}): {name}")
            t = np.asarray(sample.translation, dtype=np.float64)
            if not np.all(np.isfinite(t)):
                report.error(f"Non-finite translation: {name}")
        return report

    def validate_animation_pose(self, pose: AnimationPose) -> ValidationReport:
        report = ValidationReport()
        for bone in pose.bones:
            q = np.asarray(bone.rotation_xyzw, dtype=np.float64)
            if not np.all(np.isfinite(q)):
                report.error(f"Non-finite quat: {bone.name}")
                continue
            n = float(np.linalg.norm(q))
            if abs(n - 1.0) > QUAT_NORM_TOL * 100:
                report.warn(f"Non-unit quat {bone.name}: {n:.6f}")
            if not np.all(np.isfinite(bone.local_matrix)):
                report.error(f"Non-finite local matrix: {bone.name}")
            if bone.parent_index is not None:
                if bone.parent_index < 0 or bone.parent_index >= pose.bone_count:
                    report.error(f"Bad parent index on {bone.name}")
        return report

    def ensure_unit_quats(self, pose: AnimationPose) -> AnimationPose:
        """Return pose with normalized local rotations (new object via matrix rewrite)."""
        from motion_engine.rendering.avatar.pose.matrix_utils import compose_trs, decompose_trs
        from motion_engine.rendering.avatar.retarget.pose_converter import PoseConverter

        anim = AnimationPose.from_pose(pose, name=pose.name)
        for bone in list(anim.bones):
            t, q, s = decompose_trs(bone.local_matrix)
            qn = q_normalize((float(q[0]), float(q[1]), float(q[2]), float(q[3])))
            anim.set_local_matrix(bone.name, compose_trs(t, np.asarray(qn), s))
        return PoseConverter().rebuild_fk(anim)


__all__ = ["ValidationReport", "RetargetValidator"]
