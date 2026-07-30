"""Proportion solver — preserve motion under different body proportions."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.retarget.scale_mapper import ScaleFactors, ScaleMapper
from motion_engine.rendering.avatar.retarget.types import MappingProfile, MotionPose, Vec3


@dataclass(frozen=True, slots=True)
class ProportionResult:
    scales: ScaleFactors
    avatar_height: float
    motion_height: float


class ProportionSolver:
    """Compare motion vs avatar limb lengths and produce scale factors."""

    def __init__(self) -> None:
        self._scale = ScaleMapper()

    def avatar_height(self, bind: BindPose, root: str, head_candidates: list[str]) -> float:
        if not bind.exists(root):
            return 1.0
        root_p = np.asarray(bind.find(root).world_position, dtype=np.float64)
        head_p = None
        for h in head_candidates:
            if bind.exists(h):
                head_p = np.asarray(bind.find(h).world_position, dtype=np.float64)
                break
        if head_p is None:
            # fallback: max bone height along up-ish axis (Y then Z)
            ys = [float(b.world_position[1]) for b in bind.bones]
            zs = [float(b.world_position[2]) for b in bind.bones]
            span_y = max(ys) - min(ys) if ys else 0.0
            span_z = max(zs) - min(zs) if zs else 0.0
            return max(span_y, span_z, 1.0)
        return float(np.linalg.norm(head_p - root_p))

    def avatar_chain_length(self, bind: BindPose, target_names: list[str]) -> float:
        total = 0.0
        positions = []
        for name in target_names:
            if not bind.exists(name):
                continue
            positions.append(np.asarray(bind.find(name).world_position, dtype=np.float64))
        for a, b in zip(positions, positions[1:]):
            total += float(np.linalg.norm(b - a))
        return total

    def solve(
        self,
        source_pose: MotionPose,
        bind: BindPose,
        profile: MappingProfile,
    ) -> ProportionResult:
        avatar_h = self.avatar_height(
            bind,
            profile.root_target,
            ["head", "Head", "neck_01", "Neck"],
        )
        motion_h = self._scale.measure_height(
            source_pose,
            "Head" if source_pose.get("Head") else profile.root_source,
            profile.root_source,
        )
        if motion_h < 1e-8:
            motion_h = avatar_h

        target_heights: dict[str, float] = {"height": avatar_h}
        # Map profile chains (source names) → approximate target lengths via mapping
        src_to_tgt = profile.source_to_targets()
        for chain_name, src_chain in profile.chains.items():
            tgt_chain: list[str] = []
            for s in src_chain:
                tgts = src_to_tgt.get(s)
                if tgts:
                    tgt_chain.append(tgts[0])
            target_heights[chain_name] = self.avatar_chain_length(bind, tgt_chain) or avatar_h

        scales = self._scale.compute(
            source_pose,
            target_heights,
            source_root=profile.root_source,
            source_head="Head",
            chains={k: list(v) for k, v in profile.chains.items()},
        )
        return ProportionResult(scales=scales, avatar_height=avatar_h, motion_height=motion_h)

    def scale_root(self, root_t: Vec3, scales: ScaleFactors) -> Vec3:
        s = scales.uniform
        return (root_t[0] * s, root_t[1] * s, root_t[2] * s)


__all__ = ["ProportionResult", "ProportionSolver"]
