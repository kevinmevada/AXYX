from __future__ import annotations

from motion_engine.rendering.avatar.retarget.factory import RetargetFactory
from motion_engine.rendering.avatar.retarget.proportion_solver import ProportionSolver
from tests.retarget.helpers import two_bone_setup


def test_proportion_solver_finite():
    engine, ctx, source, target, bind = two_bone_setup()
    factory = RetargetFactory()
    skel, motions = factory.synthetic_gait(n_frames=2)
    # Use clinical motion against two-bone — still should return finite scales via profile chains
    from motion_engine.rendering.avatar.retarget.mapping_factory import matlab_to_army_girl

    prop = ProportionSolver().solve(motions[0], bind, matlab_to_army_girl())
    assert prop.scales.uniform > 0
    assert math_isfinite(prop.avatar_height)


def math_isfinite(x: float) -> bool:
    import math

    return math.isfinite(x)
