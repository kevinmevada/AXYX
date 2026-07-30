"""RetargetEngine — MotionSkeleton pose → Avatar AnimationPose."""

from __future__ import annotations

import time
from typing import Sequence

from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.pose.matrix_utils import decompose_trs
from motion_engine.rendering.avatar.pose.pose import AnimationPose
from motion_engine.rendering.avatar.retarget._quat import q_mul, q_normalize
from motion_engine.rendering.avatar.retarget.bone_mapping import BoneMapping
from motion_engine.rendering.avatar.retarget.constraint_solver import ConstraintSolver
from motion_engine.rendering.avatar.retarget.coordinate_mapper import CoordinateMapper
from motion_engine.rendering.avatar.retarget.filters import FilterConfig, TemporalFilter
from motion_engine.rendering.avatar.retarget.joint_mapping import JointMapping
from motion_engine.rendering.avatar.retarget.offset_solver import OffsetSolver
from motion_engine.rendering.avatar.retarget.pose_converter import PoseConverter
from motion_engine.rendering.avatar.retarget.proportion_solver import ProportionSolver
from motion_engine.rendering.avatar.retarget.retarget_context import RetargetContext
from motion_engine.rendering.avatar.retarget.retarget_session import RetargetSession
from motion_engine.rendering.avatar.retarget.root_motion import RootMotionProcessor
from motion_engine.rendering.avatar.retarget.rotation_mapper import RotationMapper
from motion_engine.rendering.avatar.retarget.translation_mapper import TranslationMapper
from motion_engine.rendering.avatar.retarget.types import (
    FilterKind,
    JointSample,
    MappingProfile,
    MotionPose,
    MotionSkeleton,
    Quat,
    RetargetStatistics,
    RootMotionMode,
    Vec3,
)
from motion_engine.rendering.avatar.retarget.validation import RetargetValidator
from motion_engine.rendering.avatar.skeleton.avatar_skeleton import AvatarSkeleton


class RetargetEngine:
    """Production motion retargeting engine.

    Does **not** mutate motion data, AvatarSkeleton, BindPose, or skinning
    runtimes. Output is a fresh :class:`AnimationPose`.
    """

    def __init__(
        self,
        profile: MappingProfile,
        *,
        root_mode: RootMotionMode = RootMotionMode.WORLD,
        filter_config: FilterConfig | None = None,
        hard_constraints: bool = False,
    ) -> None:
        self.profile = profile
        self.root_mode = root_mode
        self.filter_config = filter_config or FilterConfig(kind=FilterKind.NONE)
        self.hard_constraints = hard_constraints

        self.coords = CoordinateMapper(profile.source_coords, profile.target_coords)
        self.rotations = RotationMapper(self.coords)
        self.translations = TranslationMapper(self.coords)
        self.bones = BoneMapping(profile)
        self.joints = JointMapping(profile)
        self.offsets = OffsetSolver()
        self.proportions = ProportionSolver()
        self.constraints = ConstraintSolver(profile.joint_limits)
        self.poses = PoseConverter()
        self.validator = RetargetValidator()

    def prepare(
        self,
        source: MotionSkeleton,
        target: AvatarSkeleton,
        bind: BindPose,
        *,
        rest_pose: MotionPose | None = None,
    ) -> RetargetContext:
        target_names = {b.name for b in target.bones}
        active, miss_src, miss_tgt = self.bones.resolve(
            set(source.joint_names),
            target_names,
            strict=False,
        )
        rest = rest_pose or MotionPose(
            joints={
                j.name: JointSample(
                    name=j.name,
                    translation=j.rest_translation,
                    rotation_xyzw=j.rest_rotation_xyzw,
                )
                for j in source.joints
            }
        )
        offset_table = self.offsets.solve(active, rest, bind)
        # proportions from rest or a synthetic height if empty
        prop = self.proportions.solve(rest, bind, self.profile)
        coverage = self.bones.coverage(source, target_names)
        stats = RetargetStatistics(
            mapped_bones=len(active),
            missing_source=len(miss_src),
            missing_target=len(miss_tgt),
            scale_ratio=prop.scales.uniform,
            coverage=coverage,
            ignored_source=len(self.profile.ignore_source),
            ignored_target=len(self.profile.ignore_target),
        )
        return RetargetContext(
            profile=self.profile,
            source=source,
            target=target,
            bind=bind,
            active_entries=active,
            offsets=offset_table,
            scales=prop.scales,
            missing_source=miss_src,
            missing_target=miss_tgt,
            target_names=target_names,
            stats=stats,
            metadata={
                "avatar_height": prop.avatar_height,
                "motion_height": prop.motion_height,
            },
        )

    def create_session(self, context: RetargetContext) -> RetargetSession:
        return RetargetSession(
            context=context,
            root_motion=RootMotionProcessor(self.root_mode),
            filter=TemporalFilter(self.filter_config),
        )

    def retarget(
        self,
        motion: MotionPose,
        context: RetargetContext,
        *,
        session: RetargetSession | None = None,
    ) -> AnimationPose:
        """Run full pipeline for one frame → AnimationPose."""
        t0 = time.perf_counter_ns()
        bind = context.bind
        scales = context.scales
        locals_q: dict[str, Quat] = {}
        locals_t: dict[str, Vec3] = {}

        # Seed unmapped bones with bind locals (identity delta)
        for bone in bind.bones:
            _, q, _ = decompose_trs(bone.local_matrix)
            locals_q[bone.name] = (
                float(q[0]),
                float(q[1]),
                float(q[2]),
                float(q[3]),
            )

        mapped = 0
        for entry in context.active_entries:
            sample = motion.get(entry.source)
            if sample is None or not sample.valid:
                continue
            # Coordinate + rotation map
            mapped_q = self.rotations.map_local(
                sample.rotation_xyzw,
                pre=entry.pre_rotation_xyzw,
                post=entry.post_rotation_xyzw,
            )
            for target in entry.targets:
                if target not in context.target_names:
                    continue
                offset_q = context.offsets.rotation(target)
                # Prefer delta from bind when source looks like absolute world-ish
                if bind.exists(target):
                    _, bind_q, _ = decompose_trs(bind.find(target).local_matrix)
                    bind_qt = (
                        float(bind_q[0]),
                        float(bind_q[1]),
                        float(bind_q[2]),
                        float(bind_q[3]),
                    )
                    # Apply offset then blend toward mapped orientation
                    q_out = q_normalize(q_mul(offset_q, mapped_q))
                    # Keep bind scale of motion: use relative delta if mapped near identity
                    delta = self.rotations.relative_to_bind(q_out, bind_qt)
                    # Soften large deltas for stability on sparse clinical maps
                    q_final = self.rotations.apply_delta(bind_qt, delta)
                else:
                    q_final = q_normalize(q_mul(offset_q, mapped_q))

                if session is not None:
                    q_final = session.filter.filter_quat(target, q_final)
                locals_q[target] = q_final
                mapped += 1

                if entry.copy_translation and bind.exists(target):
                    raw_t = sample.world_position or sample.translation
                    if (
                        motion.root_translation is not None
                        and entry.source == context.profile.root_source
                    ):
                        raw_t = motion.root_translation
                    mapped_t = self.translations.map(raw_t)
                    mapped_t = (
                        mapped_t[0] * scales.uniform,
                        mapped_t[1] * scales.uniform,
                        mapped_t[2] * scales.uniform,
                    )
                    frame_i = session.frames_processed if session else motion.index
                    rm = session.root_motion if session is not None else RootMotionProcessor(self.root_mode)
                    mapped_t = rm.process_translation(mapped_t, frame_index=frame_i)
                    if session is not None:
                        mapped_t = session.filter.filter_vec(target, mapped_t)
                    bt = bind.find(target).translation
                    if self.root_mode == RootMotionMode.IN_PLACE:
                        locals_t[target] = (float(bt[0]), float(bt[1]), float(bt[2]))
                    elif self.root_mode == RootMotionMode.EXTRACT:
                        # Keep bind planar; preserve vertical from motion
                        up = mapped_t[2] if abs(mapped_t[2]) >= abs(mapped_t[1]) else mapped_t[1]
                        if abs(mapped_t[2]) >= abs(mapped_t[1]):
                            locals_t[target] = (float(bt[0]), float(bt[1]), float(up))
                        else:
                            locals_t[target] = (float(bt[0]), float(up), float(bt[2]))
                    else:
                        locals_t[target] = (
                            float(mapped_t[0]),
                            float(mapped_t[1]),
                            float(mapped_t[2]),
                        )

        # Constraints
        cresult = self.constraints.apply(locals_q, hard_fail=self.hard_constraints)
        locals_q = cresult.rotations

        pose = self.poses.convert(
            bind,
            locals_q,
            locals_t,
            name=f"retarget@{motion.time:.4f}",
        )
        pose = self.validator.ensure_unit_quats(pose)

        t1 = time.perf_counter_ns()
        stats = RetargetStatistics(
            mapped_bones=mapped,
            missing_source=len(context.missing_source),
            missing_target=len(context.missing_target),
            scale_ratio=scales.uniform,
            constraint_violations=cresult.violations,
            coverage=context.stats.coverage,
            frame_time_ns=t1 - t0,
            retarget_time_ns=t1 - t0,
            extra={"time": motion.time, "index": motion.index},
        )
        context.stats = stats
        if session is not None:
            session.frames_processed += 1
            session.last_pose = pose
            session.history.append(stats)
        return pose

    def retarget_sequence(
        self,
        motions: Sequence[MotionPose],
        context: RetargetContext,
    ) -> list[AnimationPose]:
        session = self.create_session(context)
        return [self.retarget(m, context, session=session) for m in motions]


__all__ = ["RetargetEngine"]
