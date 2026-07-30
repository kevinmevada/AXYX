"""Scale / proportion compensation between motion and avatar skeletons."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from motion_engine.rendering.avatar.retarget.types import MotionPose, MotionSkeleton, Vec3


@dataclass(frozen=True, slots=True)
class ScaleFactors:
    """Uniform and per-chain scale ratios."""

    uniform: float = 1.0
    height_ratio: float = 1.0
    leg_ratio: float = 1.0
    arm_ratio: float = 1.0
    torso_ratio: float = 1.0
    chain_scales: dict[str, float] | None = None

    def for_chain(self, name: str) -> float:
        if self.chain_scales and name in self.chain_scales:
            return float(self.chain_scales[name])
        low = name.lower()
        if "leg" in low or "thigh" in low or "calf" in low:
            return self.leg_ratio
        if "arm" in low or "upperarm" in low or "lowerarm" in low:
            return self.arm_ratio
        if "spine" in low or "torso" in low or "thorax" in low:
            return self.torso_ratio
        return self.uniform


class ScaleMapper:
    """Compute and apply scale compensation."""

    def measure_height(self, pose: MotionPose, head: str, root: str) -> float:
        h = pose.get(head)
        r = pose.get(root)
        if h is None or r is None:
            return 0.0
        hp = h.world_position or h.translation
        rp = r.world_position or r.translation
        return float(np.linalg.norm(np.asarray(hp) - np.asarray(rp)))

    def measure_chain_length(self, pose: MotionPose, chain: list[str]) -> float:
        total = 0.0
        for a, b in zip(chain, chain[1:]):
            ja, jb = pose.get(a), pose.get(b)
            if ja is None or jb is None:
                continue
            pa = np.asarray(ja.world_position or ja.translation, dtype=np.float64)
            pb = np.asarray(jb.world_position or jb.translation, dtype=np.float64)
            total += float(np.linalg.norm(pb - pa))
        return total

    def compute(
        self,
        source_pose: MotionPose,
        target_heights: dict[str, float],
        *,
        source_root: str = "Pelvis",
        source_head: str = "Head",
        chains: dict[str, list[str]] | None = None,
    ) -> ScaleFactors:
        src_h = self.measure_height(source_pose, source_head, source_root)
        tgt_h = float(target_heights.get("height", src_h or 1.0))
        height_ratio = (tgt_h / src_h) if src_h > 1e-8 else 1.0

        chain_scales: dict[str, float] = {}
        leg_ratio = arm_ratio = torso_ratio = height_ratio
        if chains:
            for name, chain in chains.items():
                sl = self.measure_chain_length(source_pose, list(chain))
                tl = float(target_heights.get(name, sl or 1.0))
                ratio = (tl / sl) if sl > 1e-8 else height_ratio
                chain_scales[name] = ratio
                low = name.lower()
                if "leg" in low:
                    leg_ratio = ratio
                elif "arm" in low:
                    arm_ratio = ratio
                elif "torso" in low or "spine" in low:
                    torso_ratio = ratio

        return ScaleFactors(
            uniform=height_ratio,
            height_ratio=height_ratio,
            leg_ratio=leg_ratio,
            arm_ratio=arm_ratio,
            torso_ratio=torso_ratio,
            chain_scales=chain_scales or None,
        )

    def scale_vector(self, v: Vec3, factor: float) -> Vec3:
        s = float(factor)
        return (v[0] * s, v[1] * s, v[2] * s)


__all__ = ["ScaleFactors", "ScaleMapper"]
