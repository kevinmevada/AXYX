"""Unreal-facing metadata for imported Motion Engine animations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from motion_engine.animation_clip import AnimationClip
from motion_engine.unreal.unreal_config import UnrealConfig


@dataclass
class UnrealMetadata:
    """Sidecar metadata consumed by Editor import utilities / Python hooks."""

    clip_name: str
    subject_id: str | None
    session_name: str | None
    source_coordinate_system: str
    target_coordinate_system: str
    units_source: str
    units_target: str
    unit_scale_factor: float
    fps: float
    n_frames: int
    n_joints: int
    root_joint: str
    retarget_profile: str | None = None
    target_skeleton: str | None = None
    chaos_ready: bool = True
    expose_sockets: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_clip(cls, clip: AnimationClip, config: UnrealConfig) -> UnrealMetadata:
        meta = clip.metadata
        return cls(
            clip_name=clip.name,
            subject_id=meta.get("subject_id"),
            session_name=meta.get("session_name"),
            source_coordinate_system=clip.coordinate_system,
            target_coordinate_system=config.target_coordinate_system,
            units_source=clip.units,
            units_target=config.unit_scale.target,
            unit_scale_factor=float(config.unit_scale.factor),
            fps=float(clip.fps),
            n_frames=int(clip.n_frames),
            n_joints=int(clip.n_joints),
            root_joint=clip.root_joint,
            retarget_profile=meta.get("retarget_profile"),
            target_skeleton=meta.get("target_skeleton"),
            chaos_ready=True,
            expose_sockets=list(config.expose_sockets),
            notes=[
                "Chaos physics, Foot IK, and ragdoll are configured Unreal-side.",
                "Import animation JSON / FBX then create AnimSequence via Editor.",
            ],
            extra={"compression": asdict(clip.compression) if hasattr(clip.compression, "__dataclass_fields__") else {}},
        )
