"""Structured validation for runtime avatar skeletons."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

import numpy as np

from motion_engine.rendering.avatar.skeleton.bone import Bone
from motion_engine.rendering.avatar.skeleton.constants import MAX_HIERARCHY_DEPTH
from motion_engine.rendering.avatar.skeleton.exceptions import SkeletonValidationError
from motion_engine.rendering.avatar.skeleton.hierarchy import detect_cycle, find_roots
from motion_engine.rendering.avatar.skeleton.transforms import (
    is_finite_matrix,
    is_singular_matrix,
    is_uniform_scale,
)
from motion_engine.rendering.avatar.skeleton.types import ValidationSeverity


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """Single validation finding."""

    code: str
    message: str
    severity: ValidationSeverity
    bone_index: int | None = None
    bone_name: str | None = None
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Aggregate validation outcome."""

    issues: tuple[ValidationIssue, ...]

    @property
    def ok(self) -> bool:
        """True when no ERROR-severity issues are present."""
        return not any(i.severity == ValidationSeverity.ERROR for i in self.issues)

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity == ValidationSeverity.ERROR)

    @property
    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity == ValidationSeverity.WARNING)

    def raise_if_invalid(self) -> None:
        """Raise :class:`SkeletonValidationError` if any errors exist."""
        if self.ok:
            return
        msgs = "; ".join(f"[{i.code}] {i.message}" for i in self.errors)
        raise SkeletonValidationError(
            msgs,
            code="SKEL_VALIDATION",
            details={"issues": [i.code for i in self.errors]},
        )


@dataclass(slots=True)
class SkeletonValidator:
    """Validate bone lists / hierarchy / transforms.

    Args:
        require_inverse_bind: If True, missing IBM is an error (skinned avatars).
        allow_multiple_roots: If False, multiple roots are an error.
    """

    require_inverse_bind: bool = False
    allow_multiple_roots: bool = True

    def validate(self, bones: Sequence[Bone]) -> ValidationReport:
        """Run the full validation suite."""
        issues: list[ValidationIssue] = []
        if not bones:
            issues.append(
                ValidationIssue(
                    code="SKEL_EMPTY",
                    message="Skeleton has no bones",
                    severity=ValidationSeverity.ERROR,
                )
            )
            return ValidationReport(tuple(issues))

        issues.extend(self._check_indices(bones))
        issues.extend(self._check_names(bones))
        issues.extend(self._check_parents(bones))
        issues.extend(self._check_roots_and_cycles(bones))
        issues.extend(self._check_orphans(bones))
        issues.extend(self._check_transforms(bones))
        issues.extend(self._check_depth(bones))
        return ValidationReport(tuple(issues))

    def _check_indices(self, bones: Sequence[Bone]) -> list[ValidationIssue]:
        out: list[ValidationIssue] = []
        seen_ids: set[int] = set()
        for i, b in enumerate(bones):
            if b.index != i:
                out.append(
                    ValidationIssue(
                        code="SKEL_INDEX_MISMATCH",
                        message=f"Bone at position {i} has index {b.index}",
                        severity=ValidationSeverity.ERROR,
                        bone_index=i,
                        bone_name=b.name,
                    )
                )
            bid = int(b.id)
            if bid in seen_ids:
                out.append(
                    ValidationIssue(
                        code="SKEL_DUP_ID",
                        message=f"Duplicate bone id {bid}",
                        severity=ValidationSeverity.ERROR,
                        bone_index=i,
                        bone_name=b.name,
                    )
                )
            seen_ids.add(bid)
        return out

    def _check_names(self, bones: Sequence[Bone]) -> list[ValidationIssue]:
        out: list[ValidationIssue] = []
        seen: dict[str, int] = {}
        for b in bones:
            if not b.name:
                out.append(
                    ValidationIssue(
                        code="SKEL_EMPTY_NAME",
                        message=f"Bone {b.index} has empty name",
                        severity=ValidationSeverity.ERROR,
                        bone_index=b.index,
                    )
                )
            if b.name in seen:
                out.append(
                    ValidationIssue(
                        code="SKEL_DUP_NAME",
                        message=f"Duplicate bone name {b.name!r}",
                        severity=ValidationSeverity.ERROR,
                        bone_index=b.index,
                        bone_name=b.name,
                        details={"first": seen[b.name]},
                    )
                )
            else:
                seen[b.name] = b.index
        return out

    def _check_parents(self, bones: Sequence[Bone]) -> list[ValidationIssue]:
        out: list[ValidationIssue] = []
        n = len(bones)
        for b in bones:
            p = b.parent_index
            if p is None:
                continue
            if p < 0 or p >= n:
                out.append(
                    ValidationIssue(
                        code="SKEL_BAD_PARENT",
                        message=f"Bone {b.name!r} has invalid parent {p}",
                        severity=ValidationSeverity.ERROR,
                        bone_index=b.index,
                        bone_name=b.name,
                        details={"parent": p},
                    )
                )
            elif p == b.index:
                out.append(
                    ValidationIssue(
                        code="SKEL_SELF_PARENT",
                        message=f"Bone {b.name!r} is its own parent",
                        severity=ValidationSeverity.ERROR,
                        bone_index=b.index,
                        bone_name=b.name,
                    )
                )
        return out

    def _check_roots_and_cycles(self, bones: Sequence[Bone]) -> list[ValidationIssue]:
        out: list[ValidationIssue] = []
        parents = [b.parent_index for b in bones]
        roots = find_roots(parents)
        if not roots:
            out.append(
                ValidationIssue(
                    code="SKEL_NO_ROOT",
                    message="Skeleton has no root bone",
                    severity=ValidationSeverity.ERROR,
                )
            )
        elif len(roots) > 1 and not self.allow_multiple_roots:
            out.append(
                ValidationIssue(
                    code="SKEL_MULTI_ROOT",
                    message=f"Multiple roots not allowed: {roots}",
                    severity=ValidationSeverity.ERROR,
                    details={"roots": list(roots)},
                )
            )
        elif len(roots) > 1:
            out.append(
                ValidationIssue(
                    code="SKEL_MULTI_ROOT",
                    message=f"Skeleton forest with {len(roots)} roots",
                    severity=ValidationSeverity.WARNING,
                    details={"roots": list(roots)},
                )
            )
        cycle = detect_cycle(parents)
        if cycle:
            out.append(
                ValidationIssue(
                    code="SKEL_CYCLE",
                    message=f"Hierarchy cycle involving {cycle}",
                    severity=ValidationSeverity.ERROR,
                    details={"cycle": list(cycle)},
                )
            )
        return out

    def _check_orphans(self, bones: Sequence[Bone]) -> list[ValidationIssue]:
        """Bones unreachable from any root (should not happen if parents valid)."""
        out: list[ValidationIssue] = []
        parents = [b.parent_index for b in bones]
        roots = find_roots(parents)
        if not roots:
            return out
        reachable: set[int] = set()
        stack = list(roots)
        child_map: dict[int, list[int]] = {i: [] for i in range(len(bones))}
        for b in bones:
            if b.parent_index is not None and 0 <= b.parent_index < len(bones):
                child_map[b.parent_index].append(b.index)
        while stack:
            u = stack.pop()
            if u in reachable:
                continue
            reachable.add(u)
            stack.extend(child_map[u])
        for b in bones:
            if b.index not in reachable:
                out.append(
                    ValidationIssue(
                        code="SKEL_ORPHAN",
                        message=f"Bone {b.name!r} unreachable from roots",
                        severity=ValidationSeverity.ERROR,
                        bone_index=b.index,
                        bone_name=b.name,
                    )
                )
        return out

    def _check_transforms(self, bones: Sequence[Bone]) -> list[ValidationIssue]:
        out: list[ValidationIssue] = []
        for b in bones:
            lm = b.local_matrix
            wm = b.world_matrix
            if not is_finite_matrix(lm) or not np.all(np.isfinite(b.local_transform.translation)):
                out.append(
                    ValidationIssue(
                        code="SKEL_NAN_LOCAL",
                        message=f"Non-finite local transform on {b.name!r}",
                        severity=ValidationSeverity.ERROR,
                        bone_index=b.index,
                        bone_name=b.name,
                    )
                )
            if not is_finite_matrix(wm):
                out.append(
                    ValidationIssue(
                        code="SKEL_NAN_WORLD",
                        message=f"Non-finite world transform on {b.name!r}",
                        severity=ValidationSeverity.ERROR,
                        bone_index=b.index,
                        bone_name=b.name,
                    )
                )
            if is_singular_matrix(lm):
                out.append(
                    ValidationIssue(
                        code="SKEL_SINGULAR_LOCAL",
                        message=f"Singular local matrix on {b.name!r}",
                        severity=ValidationSeverity.ERROR,
                        bone_index=b.index,
                        bone_name=b.name,
                    )
                )
            if any(abs(s) < 1e-15 for s in b.scale):
                out.append(
                    ValidationIssue(
                        code="SKEL_ZERO_SCALE",
                        message=f"Zero/near-zero scale on {b.name!r}",
                        severity=ValidationSeverity.ERROR,
                        bone_index=b.index,
                        bone_name=b.name,
                    )
                )
            if not is_uniform_scale(b.scale):
                out.append(
                    ValidationIssue(
                        code="SKEL_NONUNIFORM_SCALE",
                        message=f"Non-uniform rest scale on {b.name!r}",
                        severity=ValidationSeverity.WARNING,
                        bone_index=b.index,
                        bone_name=b.name,
                    )
                )
            if self.require_inverse_bind and b.inverse_bind is None:
                out.append(
                    ValidationIssue(
                        code="SKEL_MISSING_IBM",
                        message=f"Missing inverse bind on {b.name!r}",
                        severity=ValidationSeverity.ERROR,
                        bone_index=b.index,
                        bone_name=b.name,
                    )
                )
            if b.inverse_bind is not None:
                if not is_finite_matrix(b.inverse_bind):
                    out.append(
                        ValidationIssue(
                            code="SKEL_NAN_IBM",
                            message=f"Non-finite inverse bind on {b.name!r}",
                            severity=ValidationSeverity.ERROR,
                            bone_index=b.index,
                            bone_name=b.name,
                        )
                    )
                elif is_singular_matrix(b.inverse_bind):
                    out.append(
                        ValidationIssue(
                            code="SKEL_SINGULAR_IBM",
                            message=f"Singular inverse bind on {b.name!r}",
                            severity=ValidationSeverity.ERROR,
                            bone_index=b.index,
                            bone_name=b.name,
                        )
                    )
        return out

    def _check_depth(self, bones: Sequence[Bone]) -> list[ValidationIssue]:
        parents = [b.parent_index for b in bones]
        max_depth = 0
        for i in range(len(bones)):
            d = 0
            cur = parents[i]
            seen: set[int] = set()
            while cur is not None and cur not in seen:
                seen.add(cur)
                d += 1
                cur = parents[cur] if 0 <= cur < len(bones) else None
            max_depth = max(max_depth, d)
        if max_depth > MAX_HIERARCHY_DEPTH:
            return [
                ValidationIssue(
                    code="SKEL_DEPTH",
                    message=f"Hierarchy depth {max_depth} exceeds {MAX_HIERARCHY_DEPTH}",
                    severity=ValidationSeverity.WARNING,
                    details={"depth": max_depth},
                )
            ]
        return []


def validate_bones(
    bones: Iterable[Bone],
    *,
    require_inverse_bind: bool = False,
    allow_multiple_roots: bool = True,
    raise_on_error: bool = False,
) -> ValidationReport:
    """Convenience wrapper around :class:`SkeletonValidator`."""
    report = SkeletonValidator(
        require_inverse_bind=require_inverse_bind,
        allow_multiple_roots=allow_multiple_roots,
    ).validate(tuple(bones))
    if raise_on_error:
        report.raise_if_invalid()
    return report


__all__ = [
    "ValidationIssue",
    "ValidationReport",
    "SkeletonValidator",
    "validate_bones",
]
