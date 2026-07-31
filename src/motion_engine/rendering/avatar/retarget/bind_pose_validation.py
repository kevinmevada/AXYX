"""Bind-pose validation — clinical rest vs avatar bind after retarget."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field

from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.pose.matrix_utils import decompose_trs
from motion_engine.rendering.avatar.pose.pose import AnimationPose
from motion_engine.rendering.avatar.retarget._quat import q_conjugate, q_mul, q_normalize
from motion_engine.rendering.avatar.retarget.types import Quat

logger = logging.getLogger(__name__)

WARN_DEG = 10.0
FAIL_DEG = 30.0


def _quat_angle_deg(a: Quat, b: Quat) -> float:
    """Geodesic angle between two unit quaternions (degrees)."""
    qa = q_normalize(a)
    qb = q_normalize(b)
    # relative = a^{-1} * b
    rel = q_mul(q_conjugate(qa), qb)
    # angle = 2 * acos(|w|)
    w = abs(float(rel[3]))
    w = min(1.0, max(0.0, w))
    return math.degrees(2.0 * math.acos(w))


@dataclass(slots=True)
class BoneAlignment:
    bone: str
    error_deg: float
    status: str  # ok | warn | fail


@dataclass(slots=True)
class BindPoseReport:
    bones: list[BoneAlignment] = field(default_factory=list)
    max_error_deg: float = 0.0
    mean_error_deg: float = 0.0
    failed: bool = False
    warned: bool = False

    def summary(self) -> str:
        lines = [
            f"Bind alignment: max={self.max_error_deg:.1f}° mean={self.mean_error_deg:.1f}°"
        ]
        for b in sorted(self.bones, key=lambda x: -x.error_deg)[:12]:
            lines.append(f"  {b.bone:20s} {b.error_deg:6.1f}°  [{b.status}]")
        return "\n".join(lines)


def validate_bind_alignment(
    retargeted: AnimationPose,
    bind: BindPose,
    *,
    mapped_targets: set[str] | None = None,
    warn_deg: float = WARN_DEG,
    fail_deg: float = FAIL_DEG,
) -> BindPoseReport:
    """Compare retargeted local rotations against bind for mapped bones."""
    report = BindPoseReport()
    errors: list[float] = []
    targets = mapped_targets or {b.name for b in bind.bones}
    for name in sorted(targets):
        if not bind.exists(name) or not retargeted.exists(name):
            continue
        _, bind_q, _ = decompose_trs(bind.find(name).local_matrix)
        bind_qt = (float(bind_q[0]), float(bind_q[1]), float(bind_q[2]), float(bind_q[3]))
        _, pose_q, _ = decompose_trs(retargeted.find(name).local_matrix)
        pose_qt = (float(pose_q[0]), float(pose_q[1]), float(pose_q[2]), float(pose_q[3]))
        err = _quat_angle_deg(bind_qt, pose_qt)
        errors.append(err)
        if err >= fail_deg:
            status = "fail"
            report.failed = True
        elif err >= warn_deg:
            status = "warn"
            report.warned = True
        else:
            status = "ok"
        report.bones.append(BoneAlignment(name, err, status))
    if errors:
        report.max_error_deg = max(errors)
        report.mean_error_deg = sum(errors) / len(errors)
    if report.failed:
        logger.error("Bind pose mapping failure:\n%s", report.summary())
    elif report.warned:
        logger.warning("Bind pose alignment warnings:\n%s", report.summary())
    else:
        logger.info("Bind pose alignment OK:\n%s", report.summary())
    return report


__all__ = [
    "BindPoseReport",
    "BoneAlignment",
    "validate_bind_alignment",
    "WARN_DEG",
    "FAIL_DEG",
]
