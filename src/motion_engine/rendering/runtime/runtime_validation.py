"""Runtime validation — pipeline, state, NaN, frame consistency."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from motion_engine.rendering.runtime.runtime_context import RuntimeContext
from motion_engine.rendering.runtime.types import RuntimePhase


@dataclass
class RuntimeValidationReport:
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


class RuntimeValidator:
    """Validate prepared context and per-frame outputs."""

    def validate_context(self, ctx: RuntimeContext, phase: RuntimePhase) -> RuntimeValidationReport:
        report = RuntimeValidationReport(metadata={"phase": phase.value})
        if phase in {RuntimePhase.PREPARED, RuntimePhase.PLAYING, RuntimePhase.PAUSED}:
            if ctx.skeleton is None:
                report.error("Missing AvatarSkeleton")
            if ctx.bind is None:
                report.error("Missing BindPose")
            if ctx.mesh is None or ctx.skin is None:
                report.error("Missing mesh/skin")
            if ctx.skinning is None:
                report.error("Missing SkinningRuntime")
            if ctx.session.playback_mode.value == "retarget":
                if ctx.retarget_engine is None or ctx.retarget_context is None:
                    report.error("Retarget not prepared")
                if not ctx.motion_poses:
                    report.warn("No motion poses loaded")
        return report

    def validate_frame(self, ctx: RuntimeContext) -> RuntimeValidationReport:
        report = RuntimeValidationReport()
        if ctx.last_pose is None:
            report.error("No AnimationPose")
            return report
        for bone in ctx.last_pose.bones:
            if not np.all(np.isfinite(bone.local_matrix)):
                report.error(f"Non-finite local matrix: {bone.name}")
            n = float(np.linalg.norm(bone.rotation_xyzw))
            if abs(n - 1.0) > 1e-3:
                report.warn(f"Non-unit quat {bone.name}: {n:.4f}")
        if ctx.last_deformed is not None:
            if not np.all(np.isfinite(ctx.last_deformed.positions)):
                report.error("Non-finite deformed positions")
            if ctx.mesh is not None and ctx.last_deformed.positions.shape[0] != ctx.mesh.vertex_count:
                report.error("Deformed vertex count mismatch")
        return report


__all__ = ["RuntimeValidationReport", "RuntimeValidator"]
