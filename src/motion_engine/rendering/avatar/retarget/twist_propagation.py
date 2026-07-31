"""Twist-bone propagation — inherit parent axial rotation after primary retarget."""

from __future__ import annotations

from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.pose.matrix_utils import decompose_trs
from motion_engine.rendering.avatar.retarget._quat import (
    q_conjugate,
    q_mul,
    q_normalize,
    swing_twist_decompose,
)
from motion_engine.rendering.avatar.retarget.types import Quat

# Parent primary bone → follower twist bones (Unreal / UE5 naming).
DEFAULT_TWIST_CHAINS: dict[str, tuple[str, ...]] = {
    "thigh_l": ("thigh_twist_01_l",),
    "thigh_r": ("thigh_twist_01_r",),
    "calf_l": ("calf_twist_01_l",),
    "calf_r": ("calf_twist_01_r",),
    "upperarm_l": ("upperarm_twist_01_l", "upperarm_twist_02_l"),
    "upperarm_r": ("upperarm_twist_01_r", "upperarm_twist_02_r"),
    "lowerarm_l": ("lowerarm_twist_01_l", "lowerarm_twist_02_l"),
    "lowerarm_r": ("lowerarm_twist_01_r", "lowerarm_twist_02_r"),
}

# Local bone axis used for twist extraction (approx limb axis).
_TWIST_AXIS = (0.0, 0.0, 1.0)


def propagate_twists(
    locals_q: dict[str, Quat],
    bind: BindPose,
    *,
    chains: dict[str, tuple[str, ...]] | None = None,
    weight: float = 0.5,
) -> dict[str, Quat]:
    """Apply a fraction of each primary bone's bind-relative twist to followers.

    Twist bones that were seeded with bind locals receive only the axial
    component so they track the limb without adding swing deformation.
    """
    chains = chains or DEFAULT_TWIST_CHAINS
    out = dict(locals_q)
    for parent, twists in chains.items():
        if parent not in out or not bind.exists(parent):
            continue
        _, bind_q, _ = decompose_trs(bind.find(parent).local_matrix)
        bind_qt: Quat = (
            float(bind_q[0]),
            float(bind_q[1]),
            float(bind_q[2]),
            float(bind_q[3]),
        )
        # delta = bind^{-1} * animated
        delta = q_normalize(q_mul(q_conjugate(bind_qt), out[parent]))
        _swing, twist = swing_twist_decompose(delta, _TWIST_AXIS)
        # Soften: slerp identity → twist by weight (approx via power on quat)
        twist = _scale_quat(twist, weight)
        for name in twists:
            if not bind.exists(name):
                continue
            _, tbind_q, _ = decompose_trs(bind.find(name).local_matrix)
            tbind: Quat = (
                float(tbind_q[0]),
                float(tbind_q[1]),
                float(tbind_q[2]),
                float(tbind_q[3]),
            )
            # animated_twist = bind_twist * parent_axial_delta
            out[name] = q_normalize(q_mul(tbind, twist))
    return out


def _scale_quat(q: Quat, t: float) -> Quat:
    """Approximate quaternion power toward identity (t in 0..1)."""
    t = max(0.0, min(1.0, float(t)))
    if t <= 0.0:
        return (0.0, 0.0, 0.0, 1.0)
    if t >= 1.0:
        return q_normalize(q)
    # Nlerp with identity
    x, y, z, w = q_normalize(q)
    if w < 0.0:
        x, y, z, w = -x, -y, -z, -w
    return q_normalize((x * t, y * t, z * t, (1.0 - t) + w * t))


__all__ = ["DEFAULT_TWIST_CHAINS", "propagate_twists"]
