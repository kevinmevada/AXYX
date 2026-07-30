"""Constraint solver — joint limits, locks, preferred axes."""

from __future__ import annotations

from dataclasses import dataclass, field

from motion_engine.rendering.avatar.retarget._quat import q_normalize, swing_twist_decompose, q_mul
from motion_engine.rendering.avatar.retarget.constants import QUAT_IDENTITY
from motion_engine.rendering.avatar.retarget.exceptions import ConstraintError
from motion_engine.rendering.avatar.retarget.joint_limits import clamp_euler, euler_xyz_to_quat, quat_to_euler_xyz
from motion_engine.rendering.avatar.retarget.types import JointLimit, Quat


@dataclass
class ConstraintResult:
    rotations: dict[str, Quat] = field(default_factory=dict)
    violations: int = 0
    details: list[str] = field(default_factory=list)


class ConstraintSolver:
    """Enforce joint limits / locks on retargeted local rotations."""

    def __init__(self, limits: list[JointLimit] | tuple[JointLimit, ...] = ()) -> None:
        self.limits = {lim.bone: lim for lim in limits}

    def apply(
        self,
        locals_q: dict[str, Quat],
        *,
        hard_fail: bool = False,
    ) -> ConstraintResult:
        result = ConstraintResult()
        for name, q in locals_q.items():
            lim = self.limits.get(name)
            if lim is None:
                result.rotations[name] = q_normalize(q)
                continue
            if lim.locked:
                result.rotations[name] = QUAT_IDENTITY
                result.violations += 1
                result.details.append(f"{name}:locked")
                continue
            e = quat_to_euler_xyz(q)
            clamped, violated = clamp_euler(e, lim)
            if violated:
                result.violations += 1
                result.details.append(f"{name}:limit {e}->{clamped}")
                if hard_fail and lim.hard:
                    raise ConstraintError(f"Hard limit violated on {name}")
                q_out = euler_xyz_to_quat(clamped)
            else:
                q_out = q_normalize(q)
            if lim.preferred_axis is not None:
                swing, twist = swing_twist_decompose(q_out, lim.preferred_axis)
                # Prefer twist about preferred axis: keep twist, damp swing slightly
                q_out = q_normalize(q_mul(swing, twist))
            result.rotations[name] = q_out
        return result


__all__ = ["ConstraintResult", "ConstraintSolver"]
