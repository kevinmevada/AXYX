"""Bridge clinical Studio skeleton playback → skinned avatar mesh (M7)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np

from motion_engine.animation_clip import AnimationClip
from motion_engine.constants import SESSION_CLASS_CALIBRATION, SESSION_CLASS_CALIBRATION_COPY
from motion_engine.rendering.avatar.retarget import RetargetFactory, RootMotionMode
from motion_engine.rendering.avatar.retarget._quat import q_from_to, q_to_matrix
from motion_engine.rendering.avatar.retarget.coordinate_mapper import CoordinateMapper
from motion_engine.rendering.avatar.retarget.motion_converter import MotionConverter
from motion_engine.rendering.avatar.retarget.types import AXYX_COORDS, Y_UP_RIGHT
from motion_engine.rendering.avatar.skinning import SkinningRuntime
from motion_engine.rendering.avatar.skinning.debug.pose_edit import reset_to_bind
from motion_engine.rendering.runtime._assets import load_army_girl_avatar
from motion_engine.skeleton import Skeleton
from motion_engine.utils import classify_session_name

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, str], None]
LANDMARK_BONES = ("head", "foot_l", "foot_r", "ball_l", "ball_r")
CLINICAL_BONE_AXIS = (0.0, 0.0, 1.0)


def _noop_progress(_pct: int, _msg: str) -> None:
    return None


@dataclass
class DigitalTwinViewportBridge:
    """Retarget + skin clinical motion onto army-girl mesh for Studio viewport."""

    factory: RetargetFactory = field(default_factory=RetargetFactory)
    skinning: SkinningRuntime = field(default_factory=SkinningRuntime)
    converter: MotionConverter = field(default_factory=MotionConverter)
    ready: bool = False
    error: str | None = None
    vertex_count: int = 0
    triangle_count: int = 0
    frame_count: int = 0
    use_bind_pose: bool = False
    _skeleton: Skeleton | None = None
    _source_skel: Any = None
    _clip: AnimationClip | None = None
    _mesh: Any = None
    _skin: Any = None
    _bind: Any = None
    _engine: Any = None
    _ctx: Any = None
    _session: Any = None
    _pv_faces: np.ndarray | None = None
    _session_key: tuple[str, str, int] | None = None
    _R_to_clinical: np.ndarray | None = None
    _stage_scale: float = 1.0
    _align_rotation: np.ndarray | None = None

    def prepare(
        self,
        skeleton: Skeleton,
        *,
        progress: ProgressCallback | None = None,
    ) -> bool:
        """Load army girl + retarget pipeline for this clinical skeleton."""
        report = progress or _noop_progress
        self.ready = False
        self.error = None
        try:
            report(5, "Validating session…")
            if skeleton.n_frames <= 0:
                raise ValueError("Skeleton has no frames")

            key = (skeleton.subject_id, skeleton.session_name, skeleton.n_frames)
            if self._session_key != key:
                self._session_key = key
                self._clip = None

            self._skeleton = skeleton
            self.frame_count = int(skeleton.n_frames)
            self.use_bind_pose = self._is_calibration_session(skeleton)
            self._source_skel = self.factory.clinical_skeleton()
            self._R_to_clinical = CoordinateMapper(
                AXYX_COORDS, Y_UP_RIGHT
            ).rotation_matrix.T

            report(15, "Building motion clip…")
            if self._clip is None:
                self._clip = AnimationClip.from_skeleton(skeleton)

            report(35, "Loading avatar mesh…")
            _skel, bind, mesh, skin = load_army_girl_avatar()

            report(55, "Building rest pose…")
            rest_motion = self._motion_from_skeleton(0)

            report(70, "Setting up retarget…")
            engine = self.factory.engine(
                "matlab_clinical_to_army_girl",
                root_mode=RootMotionMode.IN_PLACE,
            )
            ctx = engine.prepare(
                self._source_skel,
                _skel,
                bind,
                rest_pose=rest_motion,
            )
            session = engine.create_session(ctx)

            self._mesh = mesh
            self._skin = skin
            self._bind = bind
            self._engine = engine
            self._ctx = ctx
            self._session = session
            self.vertex_count = int(mesh.vertex_count)
            self.triangle_count = int(mesh.triangle_count)
            self._pv_faces = np.hstack(
                [
                    np.full((mesh.triangle_count, 1), 3, dtype=np.int64),
                    mesh.indices.reshape(-1, 3).astype(np.int64),
                ]
            ).ravel()

            report(90, "Verifying skinning…")
            probe = self.deform(0)
            if probe is None:
                raise RuntimeError("First avatar frame failed to deform")
            self._calibrate_stage()

            self.ready = True
            report(100, "Avatar ready")
            logger.info(
                "Digital twin ready: verts=%d frames=%d scale=%.2f bind=%s %s/%s",
                self.vertex_count,
                self.frame_count,
                self._stage_scale,
                self.use_bind_pose,
                skeleton.subject_id,
                skeleton.session_name,
            )
            return True
        except Exception as exc:  # noqa: BLE001
            self.error = str(exc)
            logger.exception("Digital twin viewport prepare failed")
            return False

    @staticmethod
    def _is_calibration_session(skeleton: Skeleton) -> bool:
        label = classify_session_name(skeleton.session_name)
        if label in (SESSION_CLASS_CALIBRATION, SESSION_CLASS_CALIBRATION_COPY):
            return True
        return "static" in skeleton.session_name.lower()

    def _clinical_pelvis(self, frame: int) -> np.ndarray:
        assert self._skeleton is not None
        root = self._skeleton.root_joint or "Pelvis"
        pose = self._skeleton.get_pose(int(frame) % self.frame_count)
        pos = pose.get_position(root)
        if pos is None or not np.all(np.isfinite(pos)):
            raise ValueError(f"Missing clinical root position for frame {frame}")
        return np.asarray(pos, dtype=np.float64)

    def _motion_from_skeleton(self, frame: int) -> Any:
        """Exact same joint positions the stick figure uses."""
        assert self._skeleton is not None and self._source_skel is not None
        idx = int(frame) % self.frame_count
        pose = self._skeleton.get_pose(idx)
        positions = {
            name: pos
            for name, pos in pose.joint_positions.items()
            if np.all(np.isfinite(pos))
        }
        rate = float(self._skeleton.sampling_rate_hz or 100.0)
        return self.converter.adapter.pose_from_positions(
            self._source_skel,
            positions,
            time=idx / max(rate, 1e-6),
            index=idx,
            bone_axis=CLINICAL_BONE_AXIS,
        )

    def _bind_animation_pose(self) -> Any:
        if self._bind is None:
            raise RuntimeError("Bind pose not loaded")
        return reset_to_bind(self._bind)

    def _avatar_pelvis(self, pose: Any) -> np.ndarray:
        if pose.exists("pelvis"):
            return np.asarray(pose.find("pelvis").global_matrix[:3, 3], dtype=np.float64)
        return np.asarray(pose.find(pose.bones[0].name).global_matrix[:3, 3], dtype=np.float64)

    def _clinical_joint(self, frame: int, name: str) -> np.ndarray | None:
        assert self._skeleton is not None
        pose = self._skeleton.get_pose(int(frame) % self.frame_count)
        pos = pose.get_position(name)
        if pos is None or not np.all(np.isfinite(pos)):
            return None
        return np.asarray(pos, dtype=np.float64)

    def _avatar_bone_point(self, pose: Any, name: str) -> np.ndarray | None:
        if not pose.exists(name):
            return None
        return np.asarray(pose.find(name).global_matrix[:3, 3], dtype=np.float64)

    def _axis_fix(self, rel: np.ndarray) -> np.ndarray:
        """Map avatar Y-up vectors into clinical Z-up frame."""
        if self._R_to_clinical is None:
            return rel
        if rel.ndim == 1:
            return (self._R_to_clinical @ rel.reshape(3, 1)).ravel()
        return (self._R_to_clinical @ rel.T).T

    @staticmethod
    def _project_on_plane(vec: np.ndarray, normal: np.ndarray) -> np.ndarray:
        n = np.asarray(normal, dtype=np.float64).reshape(3)
        n_norm = float(np.linalg.norm(n))
        if n_norm < 1e-9:
            return np.zeros(3, dtype=np.float64)
        n = n / n_norm
        v = np.asarray(vec, dtype=np.float64).reshape(3)
        return v - np.dot(v, n) * n

    def _frame_align_rotation(
        self,
        frame: int,
        pose: Any,
        avatar_pelvis: np.ndarray,
    ) -> np.ndarray:
        """Pelvis-anchored similarity rotation: avatar bind/retarget → clinical stick."""
        clinical_pelvis = self._clinical_pelvis(frame)
        clinical_head = self._clinical_joint(frame, "Head")
        avatar_head = self._avatar_bone_point(pose, "head")
        if clinical_head is None or avatar_head is None:
            return np.eye(3, dtype=np.float64)

        up_av = self._axis_fix(avatar_head - avatar_pelvis)
        up_clin = clinical_head - clinical_pelvis
        up_av_norm = float(np.linalg.norm(up_av))
        up_clin_norm = float(np.linalg.norm(up_clin))
        if up_av_norm < 1e-6 or up_clin_norm < 1e-6:
            return np.eye(3, dtype=np.float64)

        r_up = q_to_matrix(q_from_to(up_av / up_av_norm, up_clin / up_clin_norm))

        clinical_foot = self._clinical_joint(frame, "LeftFoot")
        if clinical_foot is None:
            clinical_foot = self._clinical_joint(frame, "LAnkle")
        avatar_foot = self._avatar_bone_point(pose, "foot_l")
        if avatar_foot is None:
            avatar_foot = self._avatar_bone_point(pose, "ball_l")
        if clinical_foot is None or avatar_foot is None:
            return r_up

        fwd_av = self._axis_fix(avatar_foot - avatar_pelvis)
        fwd_clin = clinical_foot - clinical_pelvis
        fwd_av = self._project_on_plane(fwd_av, up_clin)
        fwd_clin = self._project_on_plane(fwd_clin, up_clin)
        av_n = float(np.linalg.norm(fwd_av))
        cl_n = float(np.linalg.norm(fwd_clin))
        if av_n < 1e-6 or cl_n < 1e-6:
            return r_up
        r_yaw = q_to_matrix(q_from_to(fwd_av / av_n, fwd_clin / cl_n))
        return r_yaw @ r_up

    def _to_clinical_space(
        self,
        points: np.ndarray,
        avatar_pelvis: np.ndarray,
        clinical_pelvis: np.ndarray,
        *,
        align_rotation: np.ndarray | None = None,
    ) -> np.ndarray:
        """Pelvis-anchored map into clinical stick-figure coordinates."""
        pts = np.asarray(points, dtype=np.float64)
        ap = np.asarray(avatar_pelvis, dtype=np.float64).reshape(3)
        cp = np.asarray(clinical_pelvis, dtype=np.float64).reshape(3)
        rel = pts - ap if pts.ndim == 1 else pts - ap
        rel = self._axis_fix(rel)
        r_align = align_rotation if align_rotation is not None else self._align_rotation
        if r_align is not None:
            if rel.ndim == 1:
                rel = (r_align @ rel.reshape(3, 1)).ravel()
            else:
                rel = (r_align @ rel.T).T
        if pts.ndim == 1:
            return rel * self._stage_scale + cp
        return rel * self._stage_scale + cp

    def _calibrate_stage(self) -> None:
        """Scale avatar to clinical stature using frame-0 pelvis→head height."""
        assert self._skeleton is not None
        defm = self.deform(0)
        pose = self._retarget_pose(0)
        if defm is None or pose is None:
            self._stage_scale = 1.0
            self._align_rotation = np.eye(3, dtype=np.float64)
            return
        av_pelvis = self._avatar_pelvis(pose)
        self._align_rotation = self._frame_align_rotation(0, pose, av_pelvis)
        clinical_head = self._clinical_joint(0, "Head")
        avatar_head = self._avatar_bone_point(pose, "head")
        if clinical_head is None or avatar_head is None:
            self._stage_scale = 1.0
            return
        up_av = self._axis_fix(avatar_head - av_pelvis)
        up_clin = clinical_head - self._clinical_pelvis(0)
        av_h = float(np.linalg.norm(up_av))
        clin_h = float(np.linalg.norm(up_clin))
        self._stage_scale = clin_h / av_h if av_h > 1e-6 else 1.0

    def _retarget_pose(self, frame: int) -> Any | None:
        if self.use_bind_pose:
            return self._bind_animation_pose()
        if self._engine is None or self._ctx is None:
            return None
        motion = self._motion_from_skeleton(frame)
        return self._engine.retarget(
            motion,
            self._ctx,
            session=self._session,
        )

    def frame_package(self, frame: int) -> tuple[np.ndarray | None, dict[str, np.ndarray]]:
        """Mesh + landmarks in the same clinical space as the stick figure."""
        defm = self.deform(frame)
        pose = self._retarget_pose(frame)
        if defm is None or pose is None:
            return None, {}
        clinical_pelvis = self._clinical_pelvis(frame)
        avatar_pelvis = self._avatar_pelvis(pose)
        align_rotation = self._frame_align_rotation(frame, pose, avatar_pelvis)
        raw = np.asarray(defm.positions, dtype=np.float64)
        mesh_pts = self._to_clinical_space(
            raw, avatar_pelvis, clinical_pelvis, align_rotation=align_rotation
        )
        landmarks: dict[str, np.ndarray] = {}
        for name in ("pelvis", *LANDMARK_BONES):
            bone_pt = self._avatar_bone_point(pose, name)
            if bone_pt is None:
                continue
            landmarks[name] = self._to_clinical_space(
                bone_pt, avatar_pelvis, clinical_pelvis, align_rotation=align_rotation
            )
        return mesh_pts, landmarks

    def deform(self, frame: int) -> Any | None:
        pose = self._retarget_pose(frame)
        if pose is None:
            return None
        return self.skinning.deform(
            self._mesh,
            self._skin,
            bind_pose=self._bind,
            pose=pose,
        )

    def deform_positions(self, frame: int) -> np.ndarray | None:
        mesh_pts, _ = self.frame_package(frame)
        return mesh_pts

    def pv_faces(self) -> np.ndarray | None:
        return self._pv_faces

    def clear(self) -> None:
        self.ready = False
        self.error = None
        self.use_bind_pose = False
        self.frame_count = 0
        self._skeleton = None
        self._source_skel = None
        self._clip = None
        self._mesh = None
        self._skin = None
        self._bind = None
        self._engine = None
        self._ctx = None
        self._session = None
        self._pv_faces = None
        self._session_key = None
        self._R_to_clinical = None
        self._stage_scale = 1.0
        self._align_rotation = None


__all__ = ["DigitalTwinViewportBridge", "ProgressCallback", "LANDMARK_BONES"]
