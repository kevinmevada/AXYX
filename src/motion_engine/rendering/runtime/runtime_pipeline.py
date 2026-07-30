"""Pipeline orchestration — motion → retarget → pose → skinning."""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from motion_engine.rendering.avatar.retarget import RetargetFactory, RootMotionMode
from motion_engine.rendering.avatar.retarget.mirror import mirror_pose
from motion_engine.rendering.avatar.retarget.types import MotionPose
from motion_engine.rendering.avatar.skinning.debug.pose_edit import reset_to_bind
from motion_engine.rendering.avatar.skinning.skinning_runtime import SkinningRuntime
from motion_engine.rendering.runtime._assets import load_avatar, try_load_motion_database
from motion_engine.rendering.runtime.constants import (
    STAGE_FRAME,
    STAGE_RETARGET,
    STAGE_SKINNING,
)
from motion_engine.rendering.runtime.exceptions import RuntimePipelineError
from motion_engine.rendering.runtime.runtime_cache import RuntimeCache
from motion_engine.rendering.runtime.runtime_configuration import RuntimeConfiguration
from motion_engine.rendering.runtime.runtime_context import RuntimeContext
from motion_engine.rendering.runtime.runtime_profiler import RuntimeProfiler
from motion_engine.rendering.runtime.runtime_session import RuntimeSession
from motion_engine.rendering.runtime.types import (
    AvatarKind,
    PipelineFrame,
    PlaybackMode,
)


class RuntimePipeline:
    """Coordinates database / avatar / retarget / skinning without mutating frozen runtimes."""

    def __init__(
        self,
        *,
        cache: RuntimeCache | None = None,
        profiler: RuntimeProfiler | None = None,
    ) -> None:
        self.cache = cache or RuntimeCache()
        self.profiler = profiler or RuntimeProfiler()
        self.retarget_factory = RetargetFactory()
        self.database: Any | None = None

    def load_database(self, path: str | None) -> Any | None:
        with self.profiler.measure("load"):
            self.database = try_load_motion_database(path)
        return self.database

    def list_subjects(self) -> list[str]:
        if self.database is None:
            return []
        return [str(s.id) for s in self.database.subjects]

    def list_trials(self, subject_id: str) -> list[str]:
        if self.database is None:
            return []
        subj = self.database.get_subject(subject_id)
        return [str(s.name) for s in subj.sessions]

    def prepare(self, session: RuntimeSession, config: RuntimeConfiguration) -> RuntimeContext:
        """Load avatar + motion stream and prepare retarget/skinning."""
        kind = session.avatar_kind
        cache_key = f"{kind.value}:{config.army_girl_fbx}:{config.metahuman_lod}"
        cached = self.cache.get("avatars", cache_key) if config.enable_cache else None
        if cached is not None:
            skel, bind, mesh, skin, avatar_name = cached
        else:
            with self.profiler.measure("load"):
                skel, bind, mesh, skin, avatar_name = load_avatar(
                    kind,
                    fbx_path=config.army_girl_fbx,
                    lod=config.metahuman_lod,
                )
            if config.enable_cache:
                self.cache.put("avatars", cache_key, (skel, bind, mesh, skin, avatar_name))

        session.avatar_name = avatar_name
        skinning = SkinningRuntime()
        ctx = RuntimeContext(
            session=session,
            skeleton=skel,
            bind=bind,
            mesh=mesh,
            skin=skin,
            skinning=skinning,
        )

        if session.playback_mode == PlaybackMode.BIND:
            ctx.last_pose = reset_to_bind(bind)
            return ctx

        if session.playback_mode == PlaybackMode.ANIMATION:
            from motion_engine.rendering.avatar.animation import AnimationFactory, AnimationPlayer

            factory = AnimationFactory()
            clips = factory.locomotion_set(bind)
            player = AnimationPlayer(bind=bind)
            player.load(clips.get("walk") or next(iter(clips.values())))
            ctx.extras["anim_player"] = player
            ctx.extras["anim_clips"] = clips
            ctx.last_pose = player.seek(0.0)
            return ctx

        # RETARGET mode
        profile = session.mapping_profile
        if kind == AvatarKind.FIXTURE or "fixture" in avatar_name:
            profile = "test_two_bone"
            session.mapping_profile = profile

        root_mode = RootMotionMode(config.root_motion)
        engine = self.retarget_factory.engine(profile, root_mode=root_mode)

        motion_skel, motions = self._build_motion_stream(session, config, profile)
        with self.profiler.measure("map"):
            rctx = engine.prepare(
                motion_skel,
                skel,
                bind,
                rest_pose=motions[0] if motions else None,
            )
            rsession = engine.create_session(rctx)

        ctx.motion_skeleton = motion_skel
        ctx.motion_poses = motions
        ctx.retarget_engine = engine
        ctx.retarget_context = rctx
        ctx.retarget_session = rsession
        return ctx

    def _build_motion_stream(
        self,
        session: RuntimeSession,
        config: RuntimeConfiguration,
        profile: str,
    ) -> tuple[Any, list[MotionPose]]:
        # Prefer synthetic clinical gait (always available). Real MATLAB session
        # can be bridged later via MotionConverter without API changes.
        if profile == "test_two_bone":
            from motion_engine.rendering.avatar.retarget.types import (
                AXYX_COORDS,
                MotionJoint,
                MotionSkeleton,
            )
            from tests.retarget.helpers import flexed_pose

            skel = MotionSkeleton(
                name="motion_arm",
                joints=(
                    MotionJoint("root", None, 0),
                    MotionJoint("forearm", "root", 1),
                ),
                coordinate_system=AXYX_COORDS,
                root="root",
            )
            n = max(1, int(config.synthetic_frames))
            motions = [flexed_pose(float(i % 45)) for i in range(n)]
            return skel, motions

        skel, motions = self.retarget_factory.synthetic_gait(
            n_frames=max(1, int(config.synthetic_frames)),
            fps=float(config.fps),
        )
        session.metadata["motion_source"] = "synthetic_clinical_gait"
        if self.database is not None and session.subject_id and session.trial_id:
            session.metadata["database_subject"] = session.subject_id
            session.metadata["database_trial"] = session.trial_id
            session.metadata["motion_source"] = "synthetic_clinical_gait+db_selection"
        return skel, motions

    def process_frame(
        self,
        ctx: RuntimeContext,
        frame_index: int,
        *,
        mirror: bool = False,
        validate: bool = False,
    ) -> PipelineFrame:
        if ctx.bind is None or ctx.mesh is None or ctx.skin is None or ctx.skinning is None:
            raise RuntimePipelineError("Pipeline context incomplete")

        t_frame = time.perf_counter_ns()
        stages: dict[str, int] = {}

        mode = ctx.session.playback_mode
        if mode == PlaybackMode.BIND:
            t0 = time.perf_counter_ns()
            ctx.last_pose = reset_to_bind(ctx.bind)
            stages["animation"] = time.perf_counter_ns() - t0
        elif mode == PlaybackMode.ANIMATION:
            player = ctx.extras.get("anim_player")
            if player is None:
                raise RuntimePipelineError("Animation player missing")
            t0 = time.perf_counter_ns()
            # Map frame index → time
            fps = 30.0
            ctx.last_pose = player.seek(frame_index / fps)
            stages["animation"] = time.perf_counter_ns() - t0
        else:
            if (
                ctx.retarget_engine is None
                or ctx.retarget_context is None
                or ctx.retarget_session is None
                or not ctx.motion_poses
            ):
                raise RuntimePipelineError("Retarget pipeline not prepared")
            motion = ctx.motion_poses[frame_index % len(ctx.motion_poses)]
            if mirror:
                motion = mirror_pose(motion)
            t0 = time.perf_counter_ns()
            ctx.last_pose = ctx.retarget_engine.retarget(
                motion, ctx.retarget_context, session=ctx.retarget_session
            )
            stages[STAGE_RETARGET] = time.perf_counter_ns() - t0

        assert ctx.last_pose is not None
        t0 = time.perf_counter_ns()
        ctx.last_deformed = ctx.skinning.deform(
            ctx.mesh, ctx.skin, bind_pose=ctx.bind, pose=ctx.last_pose
        )
        stages[STAGE_SKINNING] = time.perf_counter_ns() - t0

        finite = bool(np.all(np.isfinite(ctx.last_deformed.positions)))
        if validate and not finite:
            raise RuntimePipelineError("Non-finite skinned positions")

        stages[STAGE_FRAME] = time.perf_counter_ns() - t_frame
        self.profiler.record_frame(stages[STAGE_FRAME])
        for k, v in stages.items():
            self.profiler.record(k, v)

        return PipelineFrame(
            index=frame_index,
            time=frame_index / 30.0,
            pose_name=ctx.last_pose.name,
            vertex_count=int(ctx.last_deformed.positions.shape[0]),
            bone_count=ctx.last_pose.bone_count,
            finite=finite,
            stages_ns=stages,
            metadata={"mode": mode.value},
        )


__all__ = ["RuntimePipeline"]
