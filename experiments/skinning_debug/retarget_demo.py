"""M6 retarget demo controller for Skinning Debug Studio (experiments only)."""

from __future__ import annotations

from dataclasses import dataclass, field

from motion_engine.rendering.avatar.pose.pose import AnimationPose
from motion_engine.rendering.avatar.retarget import RetargetFactory, RootMotionMode
from motion_engine.rendering.avatar.retarget.constants import (
    PROFILE_MATLAB_ARMY,
    PROFILE_TEST_TWO_BONE,
)
from motion_engine.rendering.avatar.retarget.mirror import mirror_pose
from motion_engine.rendering.avatar.retarget.retarget_engine import RetargetEngine
from motion_engine.rendering.avatar.retarget.retarget_session import RetargetSession
from motion_engine.rendering.avatar.retarget.types import MotionPose, MotionSkeleton
from motion_engine.rendering.avatar.skeleton.avatar_skeleton import AvatarSkeleton
from motion_engine.rendering.avatar.pose.bind_pose import BindPose


@dataclass
class RetargetDemo:
    """Clinical gait → avatar pose stream for the debug viewer."""

    factory: RetargetFactory = field(default_factory=RetargetFactory)
    engine: RetargetEngine | None = None
    session: RetargetSession | None = None
    source: MotionSkeleton | None = None
    motions: list[MotionPose] = field(default_factory=list)
    index: int = 0
    playing: bool = False
    mirrored: bool = False
    overlay_source: bool = True
    profile_name: str = PROFILE_MATLAB_ARMY
    scale_display: float = 1.0
    last_stats: dict = field(default_factory=dict)
    source_positions: list[tuple[float, float, float]] = field(default_factory=list)
    motion_source: str = "synthetic"

    def setup(
        self,
        skeleton: AvatarSkeleton,
        bind: BindPose,
        *,
        n_frames: int = 60,
        fps: float = 30.0,
        root_mode: RootMotionMode = RootMotionMode.WORLD,
        profile_name: str | None = None,
        clinical_motions: list[MotionPose] | None = None,
        clinical_source: MotionSkeleton | None = None,
    ) -> None:
        bone_names = {b.name for b in skeleton.bones}
        if profile_name is not None:
            self.profile_name = profile_name
        elif "pelvis" in bone_names or "thigh_l" in bone_names:
            self.profile_name = PROFILE_MATLAB_ARMY
        else:
            self.profile_name = PROFILE_TEST_TWO_BONE

        if clinical_motions:
            self.motions = list(clinical_motions)
            self.source = clinical_source or self.factory.clinical_skeleton()
            self.motion_source = "clinical_matlab"
        else:
            self.source, self.motions = self.factory.synthetic_gait(n_frames=n_frames, fps=fps)
            self.motion_source = "synthetic_clinical_gait"

        if self.profile_name == PROFILE_TEST_TWO_BONE and not clinical_motions:
            # Drive two-bone with simple flexed sequence instead
            from tests.retarget.helpers import flexed_pose

            self.motions = [flexed_pose(float(i % 40)) for i in range(n_frames)]
            from motion_engine.rendering.avatar.retarget.types import MotionJoint, AXYX_COORDS

            self.source = MotionSkeleton(
                name="motion_arm",
                joints=(
                    MotionJoint("root", None, 0),
                    MotionJoint("forearm", "root", 1),
                ),
                coordinate_system=AXYX_COORDS,
                root="root",
            )

        self.engine = self.factory.engine(self.profile_name, root_mode=root_mode)
        ctx = self.engine.prepare(
            self.source,
            skeleton,
            bind,
            rest_pose=self.motions[0] if self.motions else None,
        )
        self.session = self.engine.create_session(ctx)
        self.index = 0
        self.scale_display = float(ctx.scales.uniform)
        self.last_stats = ctx.stats.as_dict()

    def current_motion(self) -> MotionPose | None:
        if not self.motions:
            return None
        m = self.motions[self.index % len(self.motions)]
        return mirror_pose(m) if self.mirrored else m

    def tick(self) -> AnimationPose | None:
        if self.engine is None or self.session is None:
            return None
        motion = self.current_motion()
        if motion is None:
            return None
        pose = self.engine.retarget(motion, self.session.context, session=self.session)
        self.last_stats = self.session.context.stats.as_dict()
        self.source_positions = []
        for sample in motion.joints.values():
            p = sample.world_position or sample.translation
            self.source_positions.append((float(p[0]), float(p[1]), float(p[2])))
        if self.playing:
            self.index = (self.index + 1) % max(len(self.motions), 1)
        return pose

    def info_text(self) -> str:
        return (
            f"profile={self.profile_name}  source={self.motion_source}  "
            f"frame={self.index}/{len(self.motions)}  "
            f"scale={self.scale_display:.3f}  "
            f"mapped={self.last_stats.get('mapped_bones', 0)}  "
            f"coverage={self.last_stats.get('coverage', 0):.2f}"
        )


def load_clinical_motions(
    subject_id: str = "S2",
    session_name: str = "WU01",
    *,
    mat_path: str | None = None,
) -> tuple[list[MotionPose], MotionSkeleton, float] | None:
    """Load real MATLAB trial motion (same data that drives the stick figure)."""
    try:
        from motion_engine.rendering.avatar.retarget.motion_converter import MotionConverter
        from motion_engine.studio.services.motion_service import MotionService

        svc = MotionService()
        svc.load_database(mat_path)
        _, clip = svc.load_session(subject_id, session_name, build_clip=True)
        if clip is None or not getattr(clip, "frames", None):
            return None
        factory = RetargetFactory()
        source = factory.clinical_skeleton()
        motions = MotionConverter().from_clip_frames(clip)
        fps = float(getattr(clip, "fps", 100.0) or 100.0)
        return motions, source, fps
    except Exception:  # noqa: BLE001
        return None


__all__ = ["RetargetDemo", "load_clinical_motions"]
