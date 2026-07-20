"""Validation suite tests."""

from __future__ import annotations

import numpy as np
import pytest

from motion_engine.rendering.avatar.skeleton import (
    Bone,
    SkeletonValidationError,
    SkeletonValidator,
    Transform,
    validate_bones,
)
from motion_engine.rendering.avatar.skeleton.transforms import identity_matrix


def _bone(i: int, name: str, parent: int | None, **kw) -> Bone:
    return Bone(
        index=i,
        name=name,
        parent_index=parent,
        local_transform=Transform.identity(),
        world_transform=identity_matrix(),
        inverse_bind=identity_matrix(),
        **kw,
    )


def test_valid_chain_ok(chain_runtime) -> None:
    report = chain_runtime.validate()
    assert report.ok


def test_empty_skeleton() -> None:
    report = validate_bones([])
    assert not report.ok
    assert report.errors[0].code == "SKEL_EMPTY"


def test_duplicate_names() -> None:
    bones = (_bone(0, "a", None), _bone(1, "a", 0))
    report = validate_bones(bones)
    assert any(i.code == "SKEL_DUP_NAME" for i in report.errors)


def test_bad_parent() -> None:
    bones = (_bone(0, "r", None), _bone(1, "x", 99))
    report = validate_bones(bones)
    assert any(i.code == "SKEL_BAD_PARENT" for i in report.errors)


def test_cycle_rejected() -> None:
    bones = (_bone(0, "a", 1), _bone(1, "b", 0))
    report = validate_bones(bones)
    assert any(i.code == "SKEL_CYCLE" for i in report.errors)


def test_nan_transform() -> None:
    bad = np.eye(4)
    bad[0, 0] = np.nan
    b = Bone(index=0, name="r", parent_index=None, world_transform=bad)
    report = validate_bones([b])
    assert any(i.code in {"SKEL_NAN_WORLD", "SKEL_NAN_LOCAL"} for i in report.errors)


def test_missing_ibm_when_required() -> None:
    b = Bone(index=0, name="r", parent_index=None, inverse_bind=None)
    report = SkeletonValidator(require_inverse_bind=True).validate([b])
    assert any(i.code == "SKEL_MISSING_IBM" for i in report.errors)


def test_raise_if_invalid() -> None:
    report = validate_bones([])
    with pytest.raises(SkeletonValidationError):
        report.raise_if_invalid()


def test_multi_root_warning() -> None:
    bones = (_bone(0, "a", None), _bone(1, "b", None))
    report = validate_bones(bones, allow_multiple_roots=True)
    assert report.ok
    assert any(i.code == "SKEL_MULTI_ROOT" for i in report.warnings)
