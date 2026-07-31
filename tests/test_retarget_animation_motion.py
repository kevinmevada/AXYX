"""Avatar retarget must animate limbs across frames (not a frozen bind mannequin)."""

from __future__ import annotations

import numpy as np
import pytest

from motion_engine.rendering.avatar.retarget.factory import RetargetFactory
from motion_engine.rendering.avatar.retarget.skeleton_adapter import (
    PREFERRED_AIM_CHILD,
    SkeletonAdapter,
)
from motion_engine.rendering.runtime.studio_viewport import DigitalTwinViewportBridge


def test_pelvis_prefers_thorax_aim() -> None:
    assert PREFERRED_AIM_CHILD["Pelvis"] == "Thorax"
    assert PREFERRED_AIM_CHILD["LHip"] == "LKnee"
    assert PREFERRED_AIM_CHILD["LShoulder"] == "LElbow"


def test_walking_sessions_are_not_bind_locked() -> None:
    """Multi-frame trials must retarget every frame (stick-matched motion)."""

    class _Skel:
        subject_id = "S1"
        session_name = "WU01"
        n_frames = 120
        sampling_rate_hz = 100.0

    bridge = DigitalTwinViewportBridge()
    sk = _Skel()
    bridge.frame_count = int(sk.n_frames)
    bridge.use_bind_pose = False
    if bridge._is_calibration_session(sk) and bridge.frame_count <= 1:  # noqa: SLF001
        bridge.use_bind_pose = True
    assert bridge.use_bind_pose is False
    assert bridge._is_calibration_session(sk) is False  # noqa: SLF001


def test_pelvis_aim_exposes_hip_swing() -> None:
    """Pelvis→Thorax aim keeps leg swing in LHip locals (not absorbed by pelvis)."""
    adapter = SkeletonAdapter()
    source = RetargetFactory().clinical_skeleton()
    rest = adapter.pose_from_positions(
        source,
        adapter.synthetic_gait_positions(source, phase=0.0),
        index=0,
        bone_axis=(0.0, 0.0, 1.0),
    )
    swung = adapter.pose_from_positions(
        source,
        adapter.synthetic_gait_positions(source, phase=0.25),
        index=1,
        bone_axis=(0.0, 0.0, 1.0),
    )
    # With thorax aim, pelvis stays near identity for upright synthetic gait.
    assert abs(float(rest.get("Pelvis").rotation_xyzw[3]) - 1.0) < 1e-5
    q0 = np.asarray(rest.get("LHip").rotation_xyzw, dtype=np.float64)
    q1 = np.asarray(swung.get("LHip").rotation_xyzw, dtype=np.float64)
    assert float(1.0 - abs(float(np.dot(q0, q1)))) > 0.01


def test_synthetic_gait_moves_skinned_mesh() -> None:
    pytest.importorskip("ufbx")
    from motion_engine.rendering.avatar.pose.matrix_utils import decompose_trs
    from motion_engine.rendering.avatar.retarget.cache import get_global_cache
    from motion_engine.rendering.avatar.retarget.constraint_solver import ConstraintSolver
    from motion_engine.rendering.avatar.retarget.constants import PROFILE_MATLAB_ARMY
    from motion_engine.rendering.avatar.retarget.types import RootMotionMode
    from motion_engine.rendering.avatar.skinning import SkinningRuntime
    from motion_engine.rendering.runtime._assets import load_army_girl_avatar

    get_global_cache().clear()
    factory = RetargetFactory()
    adapter = SkeletonAdapter()
    source = factory.clinical_skeleton()
    try:
        target, bind, mesh, skin = load_army_girl_avatar()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Army Girl FBX unavailable: {exc}")

    engine = factory.engine(PROFILE_MATLAB_ARMY, root_mode=RootMotionMode.IN_PLACE)
    engine.constraints = ConstraintSolver(())
    rest = adapter.pose_from_positions(
        source,
        adapter.synthetic_gait_positions(source, phase=0.0),
        index=0,
        bone_axis=(0.0, 0.0, 1.0),
    )
    ctx = engine.prepare(source, target, bind, rest_pose=rest)
    session = engine.create_session(ctx)
    skinning = SkinningRuntime()

    def _mesh_at(phase: float, index: int) -> tuple[np.ndarray, np.ndarray]:
        motion = adapter.pose_from_positions(
            source,
            adapter.synthetic_gait_positions(source, phase=phase),
            index=index,
            bone_axis=(0.0, 0.0, 1.0),
        )
        pose = engine.retarget(motion, ctx, session=session)
        _, thigh_q, _ = decompose_trs(pose.find("thigh_l").local_matrix)
        deformed = skinning.deform(mesh, skin, bind_pose=bind, pose=pose)
        return np.asarray(deformed.positions, dtype=np.float64), np.asarray(
            thigh_q, dtype=np.float64
        )

    pts0, q0 = _mesh_at(0.0, 0)
    pts1, q1 = _mesh_at(0.25, 1)
    mesh_delta = float(np.linalg.norm(pts1 - pts0, axis=1).max())
    quat_delta = float(1.0 - abs(float(np.dot(q0, q1))))
    assert mesh_delta > 20.0, f"skinned mesh barely moved ({mesh_delta})"
    assert quat_delta > 0.01, f"thigh local rotation barely changed ({quat_delta})"
