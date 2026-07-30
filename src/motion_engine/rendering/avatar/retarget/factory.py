"""Factory — build engines, sessions, synthetic motion, profiles."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.retarget.cache import RetargetCache, get_global_cache
from motion_engine.rendering.avatar.retarget.constants import PROFILE_MATLAB_ARMY, RUNTIME_VERSION
from motion_engine.rendering.avatar.retarget.filters import FilterConfig
from motion_engine.rendering.avatar.retarget.mapping_factory import MappingFactory
from motion_engine.rendering.avatar.retarget.motion_converter import MotionConverter
from motion_engine.rendering.avatar.retarget.retarget_context import RetargetContext
from motion_engine.rendering.avatar.retarget.retarget_engine import RetargetEngine
from motion_engine.rendering.avatar.retarget.retarget_session import RetargetSession
from motion_engine.rendering.avatar.retarget.skeleton_adapter import SkeletonAdapter
from motion_engine.rendering.avatar.retarget.types import (
    FilterKind,
    MappingProfile,
    MotionPose,
    MotionSkeleton,
    RootMotionMode,
)
from motion_engine.rendering.avatar.skeleton.avatar_skeleton import AvatarSkeleton


class RetargetFactory:
    """High-level construction helpers for research & studio."""

    def __init__(self, cache: RetargetCache | None = None) -> None:
        self.mappings = MappingFactory()
        self.adapter = SkeletonAdapter()
        self.converter = MotionConverter()
        self.cache = cache or get_global_cache()

    @property
    def version(self) -> str:
        return RUNTIME_VERSION

    def profile(self, name: str = PROFILE_MATLAB_ARMY) -> MappingProfile:
        cached = self.cache.get_profile(name)
        if cached is not None:
            return cached
        profile = self.mappings.builtin(name)
        self.cache.put_profile(profile)
        return profile

    def profile_from_json(self, path: str | Path) -> MappingProfile:
        profile = self.mappings.from_json(path)
        self.cache.put_profile(profile)
        return profile

    def engine(
        self,
        profile: MappingProfile | str | None = None,
        *,
        root_mode: RootMotionMode = RootMotionMode.WORLD,
        filter_kind: FilterKind = FilterKind.NONE,
        filter_window: int = 5,
        hard_constraints: bool = False,
    ) -> RetargetEngine:
        if profile is None:
            prof = self.profile()
        elif isinstance(profile, str):
            prof = self.profile(profile)
        else:
            prof = profile
        return RetargetEngine(
            prof,
            root_mode=root_mode,
            filter_config=FilterConfig(kind=filter_kind, window=filter_window),
            hard_constraints=hard_constraints,
        )

    def clinical_skeleton(self) -> MotionSkeleton:
        return self.adapter.clinical_skeleton()

    def prepare(
        self,
        source: MotionSkeleton,
        target: AvatarSkeleton,
        bind: BindPose,
        *,
        profile: MappingProfile | str | None = None,
    ) -> tuple[RetargetEngine, RetargetContext]:
        eng = self.engine(profile)
        key = (eng.profile.name, source.name, target.name, bind.name, len(bind.bones))
        cached = self.cache.get_context(key)
        if cached is not None:
            return eng, cached
        ctx = eng.prepare(source, target, bind)
        self.cache.put_context(key, ctx)
        return eng, ctx

    def session(
        self,
        source: MotionSkeleton,
        target: AvatarSkeleton,
        bind: BindPose,
        *,
        profile: MappingProfile | str | None = None,
    ) -> tuple[RetargetEngine, RetargetSession]:
        eng, ctx = self.prepare(source, target, bind, profile=profile)
        return eng, eng.create_session(ctx)

    def synthetic_gait(
        self,
        *,
        n_frames: int = 60,
        fps: float = 30.0,
        skeleton: MotionSkeleton | None = None,
    ) -> tuple[MotionSkeleton, list[MotionPose]]:
        skel = skeleton or self.clinical_skeleton()
        poses = list(self.converter.iter_gait(skel, n_frames=n_frames, fps=fps))
        return skel, poses

    def retarget_gait(
        self,
        target: AvatarSkeleton,
        bind: BindPose,
        *,
        profile: MappingProfile | str = PROFILE_MATLAB_ARMY,
        n_frames: int = 60,
        fps: float = 30.0,
        root_mode: RootMotionMode = RootMotionMode.WORLD,
    ) -> list:
        skel, motions = self.synthetic_gait(n_frames=n_frames, fps=fps)
        eng = self.engine(profile, root_mode=root_mode)
        ctx = eng.prepare(skel, target, bind, rest_pose=motions[0] if motions else None)
        return eng.retarget_sequence(motions, ctx)


__all__ = ["RetargetFactory"]
