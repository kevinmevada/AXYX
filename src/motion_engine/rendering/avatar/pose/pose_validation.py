"""Pose validation with structured diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

from motion_engine.rendering.avatar.pose.bind_matrix import validate_ibm_against_world
from motion_engine.rendering.avatar.pose.constants import (
    DET_NEAR_ONE_EPS,
    PROPAGATION_MATCH_EPS,
    QUAT_UNIT_EPS,
)
from motion_engine.rendering.avatar.pose.exceptions import PoseValidationError
from motion_engine.rendering.avatar.pose.matrix_utils import (
    determinant3,
    is_finite,
    is_rotation_orthogonal,
    is_singular,
    is_unit_quat,
)
from motion_engine.rendering.avatar.pose.pose import BonePose, Pose
from motion_engine.rendering.avatar.pose.transform_propagation import verify_propagation
from motion_engine.rendering.avatar.pose.types import ValidationSeverity


@dataclass(frozen=True, slots=True)
class PoseValidationIssue:
    """Single pose validation finding."""

    code: str
    message: str
    severity: ValidationSeverity
    bone_index: int | None = None
    bone_name: str | None = None
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PoseValidationReport:
    """Aggregate pose validation outcome."""

    issues: tuple[PoseValidationIssue, ...]

    @property
    def ok(self) -> bool:
        return not any(i.severity == ValidationSeverity.ERROR for i in self.issues)

    @property
    def errors(self) -> tuple[PoseValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity == ValidationSeverity.ERROR)

    @property
    def warnings(self) -> tuple[PoseValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity == ValidationSeverity.WARNING)

    def raise_if_invalid(self) -> None:
        if self.ok:
            return
        msgs = "; ".join(f"[{i.code}] {i.message}" for i in self.errors)
        raise PoseValidationError(
            msgs,
            code="POSE_VALIDATION",
            details={"issues": [i.code for i in self.errors]},
        )


@dataclass(slots=True)
class PoseValidator:
    """Validate bind / runtime poses mathematically."""

    check_ibm_identity: bool = True
    check_propagation: bool = True
    require_root: bool = True

    def validate(self, pose: Pose) -> PoseValidationReport:
        bones = pose.bones
        issues: list[PoseValidationIssue] = []
        if not bones:
            issues.append(
                PoseValidationIssue(
                    code="POSE_EMPTY",
                    message="Pose has no bones",
                    severity=ValidationSeverity.ERROR,
                )
            )
            return PoseValidationReport(tuple(issues))

        issues.extend(self._check_identity(bones))
        issues.extend(self._check_matrices(bones))
        issues.extend(self._check_hierarchy(bones))
        if self.check_propagation:
            issues.extend(self._check_fk(bones))
        if self.check_ibm_identity:
            issues.extend(self._check_ibm(bones))
        return PoseValidationReport(tuple(issues))

    def _check_identity(self, bones: Sequence[BonePose]) -> list[PoseValidationIssue]:
        out: list[PoseValidationIssue] = []
        names: dict[str, int] = {}
        for i, b in enumerate(bones):
            if b.index != i:
                out.append(
                    PoseValidationIssue(
                        code="POSE_INDEX_MISMATCH",
                        message=f"Bone at {i} has index {b.index}",
                        severity=ValidationSeverity.ERROR,
                        bone_index=i,
                        bone_name=b.name,
                    )
                )
            if b.name in names:
                out.append(
                    PoseValidationIssue(
                        code="POSE_DUP_NAME",
                        message=f"Duplicate bone pose name {b.name!r}",
                        severity=ValidationSeverity.ERROR,
                        bone_index=i,
                        bone_name=b.name,
                    )
                )
            else:
                names[b.name] = i
        return out

    def _check_matrices(self, bones: Sequence[BonePose]) -> list[PoseValidationIssue]:
        out: list[PoseValidationIssue] = []
        for b in bones:
            for label, m in (
                ("local", b.local_matrix),
                ("global", b.global_matrix),
                ("rest", b.rest_matrix),
                ("ibm", b.inverse_bind_matrix),
            ):
                if not is_finite(m):
                    out.append(
                        PoseValidationIssue(
                            code="POSE_NAN",
                            message=f"Non-finite {label} matrix on {b.name!r}",
                            severity=ValidationSeverity.ERROR,
                            bone_index=b.index,
                            bone_name=b.name,
                        )
                    )
            if is_singular(b.local_matrix):
                out.append(
                    PoseValidationIssue(
                        code="POSE_SINGULAR_LOCAL",
                        message=f"Singular local matrix on {b.name!r}",
                        severity=ValidationSeverity.ERROR,
                        bone_index=b.index,
                        bone_name=b.name,
                    )
                )
            if is_singular(b.inverse_bind_matrix):
                out.append(
                    PoseValidationIssue(
                        code="POSE_SINGULAR_IBM",
                        message=f"Singular inverse bind on {b.name!r}",
                        severity=ValidationSeverity.ERROR,
                        bone_index=b.index,
                        bone_name=b.name,
                    )
                )
            if not is_unit_quat(b.rotation_xyzw, eps=QUAT_UNIT_EPS):
                out.append(
                    PoseValidationIssue(
                        code="POSE_QUAT_NORM",
                        message=f"Non-unit quaternion on {b.name!r}",
                        severity=ValidationSeverity.WARNING,
                        bone_index=b.index,
                        bone_name=b.name,
                    )
                )
            # Orthogonality of rotation part (warn on strong non-ortho)
            if not is_rotation_orthogonal(b.local_matrix):
                # Scales break orthogonality — only warn when scale ~ uniform unit
                if abs(b.scale[0] - 1.0) < 1e-3 and abs(b.scale[1] - 1.0) < 1e-3:
                    out.append(
                        PoseValidationIssue(
                            code="POSE_NON_ORTHO",
                            message=f"Local rotation not orthogonal on {b.name!r}",
                            severity=ValidationSeverity.WARNING,
                            bone_index=b.index,
                            bone_name=b.name,
                        )
                    )
            det = abs(determinant3(b.global_matrix))
            if det < DET_NEAR_ONE_EPS and not is_singular(b.global_matrix):
                pass  # scaled matrices OK
        return out

    def _check_hierarchy(self, bones: Sequence[BonePose]) -> list[PoseValidationIssue]:
        out: list[PoseValidationIssue] = []
        n = len(bones)
        roots = [b for b in bones if b.parent_index is None]
        if self.require_root and not roots:
            out.append(
                PoseValidationIssue(
                    code="POSE_NO_ROOT",
                    message="Pose has no root transform",
                    severity=ValidationSeverity.ERROR,
                )
            )
        for b in bones:
            p = b.parent_index
            if p is None:
                continue
            if p < 0 or p >= n:
                out.append(
                    PoseValidationIssue(
                        code="POSE_BAD_PARENT",
                        message=f"Invalid parent {p} on {b.name!r}",
                        severity=ValidationSeverity.ERROR,
                        bone_index=b.index,
                        bone_name=b.name,
                    )
                )
            elif p == b.index:
                out.append(
                    PoseValidationIssue(
                        code="POSE_SELF_PARENT",
                        message=f"Self-parent on {b.name!r}",
                        severity=ValidationSeverity.ERROR,
                        bone_index=b.index,
                        bone_name=b.name,
                    )
                )
            else:
                # children consistency
                if b.index not in bones[p].children:
                    out.append(
                        PoseValidationIssue(
                            code="POSE_CHILD_MISMATCH",
                            message=f"Parent {bones[p].name!r} missing child {b.name!r}",
                            severity=ValidationSeverity.ERROR,
                            bone_index=b.index,
                            bone_name=b.name,
                        )
                    )
        return out

    def _check_fk(self, bones: Sequence[BonePose]) -> list[PoseValidationIssue]:
        locals_m = [b.local_matrix for b in bones]
        worlds = [b.global_matrix for b in bones]
        parents = [b.parent_index for b in bones]
        bad = verify_propagation(locals_m, worlds, parents, eps=PROPAGATION_MATCH_EPS)
        return [
            PoseValidationIssue(
                code="POSE_FK_MISMATCH",
                message=f"World transform mismatch vs FK on {bones[i].name!r}",
                severity=ValidationSeverity.ERROR,
                bone_index=i,
                bone_name=bones[i].name,
            )
            for i in bad
        ]

    def _check_ibm(self, bones: Sequence[BonePose]) -> list[PoseValidationIssue]:
        out: list[PoseValidationIssue] = []
        for b in bones:
            if not validate_ibm_against_world(b.rest_matrix, b.inverse_bind_matrix):
                # Authoring may store IBM relative to bind world; try global
                if not validate_ibm_against_world(b.global_matrix, b.inverse_bind_matrix):
                    out.append(
                        PoseValidationIssue(
                            code="POSE_IBM_MISMATCH",
                            message=f"IBM does not invert rest/world on {b.name!r}",
                            severity=ValidationSeverity.WARNING,
                            bone_index=b.index,
                            bone_name=b.name,
                        )
                    )
        return out


def validate_pose(pose: Pose, *, raise_on_error: bool = False) -> PoseValidationReport:
    """Convenience validator."""
    report = PoseValidator().validate(pose)
    if raise_on_error:
        report.raise_if_invalid()
    return report


__all__ = [
    "PoseValidationIssue",
    "PoseValidationReport",
    "PoseValidator",
    "validate_pose",
]
