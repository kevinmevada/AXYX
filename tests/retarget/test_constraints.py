from __future__ import annotations

import math

import pytest

from motion_engine.rendering.avatar.retarget._quat import q_axis_angle
from motion_engine.rendering.avatar.retarget.constraint_solver import ConstraintSolver
from motion_engine.rendering.avatar.retarget.exceptions import ConstraintError
from motion_engine.rendering.avatar.retarget.types import JointLimit


def test_soft_clamp():
    lim = JointLimit(bone="forearm", min_xyz=(-0.1, -0.1, -0.1), max_xyz=(0.1, 0.1, 0.1))
    cs = ConstraintSolver([lim])
    q = q_axis_angle((0, 0, 1), math.radians(45))
    res = cs.apply({"forearm": q})
    assert res.violations >= 1
    assert "forearm" in res.rotations


def test_hard_fail():
    lim = JointLimit(
        bone="forearm",
        min_xyz=(-0.01, -0.01, -0.01),
        max_xyz=(0.01, 0.01, 0.01),
        hard=True,
    )
    cs = ConstraintSolver([lim])
    q = q_axis_angle((0, 0, 1), 1.0)
    with pytest.raises(ConstraintError):
        cs.apply({"forearm": q}, hard_fail=True)
