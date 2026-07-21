"""Weight table and skinning input validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

from motion_engine.rendering.avatar.skinning.constants import (
    UNUSED_BONE_INDEX,
    WEIGHT_NONNEG_EPS,
    WEIGHT_SUM_EPS,
)
from motion_engine.rendering.avatar.skinning.exceptions import SkinningValidationError
from motion_engine.rendering.avatar.skinning.types import ValidationSeverity
from motion_engine.rendering.avatar.skinning.weight_table import WeightTable


@dataclass(frozen=True, slots=True)
class WeightValidationIssue:
    code: str
    message: str
    severity: ValidationSeverity
    vertex_index: int | None = None
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WeightValidationReport:
    issues: tuple[WeightValidationIssue, ...]

    @property
    def ok(self) -> bool:
        return not any(i.severity == ValidationSeverity.ERROR for i in self.issues)

    @property
    def errors(self) -> tuple[WeightValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity == ValidationSeverity.ERROR)

    def raise_if_invalid(self) -> None:
        if self.ok:
            return
        msgs = "; ".join(f"[{i.code}] {i.message}" for i in self.errors)
        raise SkinningValidationError(msgs, details={"codes": [i.code for i in self.errors]})


def validate_weight_table(
    table: WeightTable,
    *,
    bone_count: int,
    vertex_count: int | None = None,
    require_unit_sum: bool = False,
) -> WeightValidationReport:
    """Validate indices, weights, duplicates, finiteness."""
    issues: list[WeightValidationIssue] = []
    if vertex_count is not None and table.vertex_count != vertex_count:
        issues.append(
            WeightValidationIssue(
                code="SKIN_VERT_MISMATCH",
                message=f"Weight rows {table.vertex_count} != mesh vertices {vertex_count}",
                severity=ValidationSeverity.ERROR,
            )
        )
    idx = table.joint_indices
    w = table.joint_weights
    if not np.all(np.isfinite(w)):
        issues.append(
            WeightValidationIssue(
                code="SKIN_WEIGHT_NAN",
                message="Non-finite weights detected",
                severity=ValidationSeverity.ERROR,
            )
        )
    if np.any(w < WEIGHT_NONNEG_EPS):
        issues.append(
            WeightValidationIssue(
                code="SKIN_NEG_WEIGHT",
                message="Negative weights detected",
                severity=ValidationSeverity.ERROR,
            )
        )
    # invalid bone indices (except unused)
    bad_idx = (idx >= bone_count) | ((idx < 0) & (idx != UNUSED_BONE_INDEX))
    if np.any(bad_idx):
        issues.append(
            WeightValidationIssue(
                code="SKIN_BAD_BONE",
                message="Bone index out of range",
                severity=ValidationSeverity.ERROR,
                details={"count": int(bad_idx.sum())},
            )
        )
    # duplicates per row (among active influences only)
    for vi in range(table.vertex_count):
        row_i = idx[vi]
        row_w = w[vi]
        used = row_i[(row_i >= 0) & (row_w > 0.0)]
        if used.size and used.size != np.unique(used).size:
            issues.append(
                WeightValidationIssue(
                    code="SKIN_DUP_INFLUENCE",
                    message=f"Duplicate bone influences on vertex {vi}",
                    severity=ValidationSeverity.ERROR,
                    vertex_index=vi,
                )
            )
            break  # one sample enough
    # sums
    used_mask = (idx >= 0) & (w > 0.0)
    sums = np.where(used_mask, w, 0.0).sum(axis=1)
    active = sums > WEIGHT_SUM_EPS
    if require_unit_sum:
        bad = active & (np.abs(sums - 1.0) > WEIGHT_SUM_EPS)
        if np.any(bad):
            issues.append(
                WeightValidationIssue(
                    code="SKIN_WEIGHT_SUM",
                    message=f"{int(bad.sum())} vertices not unit-sum",
                    severity=ValidationSeverity.ERROR,
                )
            )
    elif np.any(active & (np.abs(sums - 1.0) > 0.05)):
        issues.append(
            WeightValidationIssue(
                code="SKIN_WEIGHT_SUM_WARN",
                message="Some vertex weights deviate from 1.0",
                severity=ValidationSeverity.WARNING,
            )
        )
    return WeightValidationReport(tuple(issues))


def validate_pose_bone_count(pose_bone_count: int, expected: int) -> None:
    if pose_bone_count != expected:
        raise SkinningValidationError(
            f"Pose bone count {pose_bone_count} != expected {expected}",
            code="SKIN_POSE_MISMATCH",
        )


__all__ = [
    "WeightValidationIssue",
    "WeightValidationReport",
    "validate_weight_table",
    "validate_pose_bone_count",
]
