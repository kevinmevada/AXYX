"""Unreal Engine 5 export configuration loaded from YAML."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from motion_engine.exceptions import MotionEngineError

DEFAULT_UNREAL_CONFIG = Path("config/unreal_config.yaml")


class UnrealConfigError(MotionEngineError):
    """Raised when Unreal config cannot be loaded."""


@dataclass(slots=True)
class UnitScale:
    source: str = "Unknown"
    target: str = "cm"
    factor: float = 0.1
    note: str = ""


@dataclass(slots=True)
class AxisRemap:
    x: str = "+x"
    y: str = "-y"
    z: str = "+z"
    source_handedness: str = "right"
    target_handedness: str = "left"
    source_up: str = "Z"
    target_up: str = "Z"


@dataclass
class UnrealConfig:
    """Typed Unreal integration settings."""

    name: str
    source_coordinate_system: str
    target_coordinate_system: str
    unit_scale: UnitScale
    axes: AxisRemap
    root_motion_enabled: bool = True
    root_joint: str = "Pelvis"
    content_path: str = "/Game/MotionEngine"
    asset_prefix: str = "ME_"
    skeleton_suffix: str = "_Skeleton"
    anim_suffix: str = "_Anim"
    enable_root_motion: bool = True
    interpolation: str = "linear"
    expose_sockets: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path | None = None) -> UnrealConfig:
        cfg_path = Path(path) if path else DEFAULT_UNREAL_CONFIG
        if not cfg_path.is_file():
            raise UnrealConfigError(f"Unreal config missing: {cfg_path}")
        raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        unit = raw.get("unit_scale") or {}
        axes = raw.get("axes") or {}
        remap = axes.get("remap") or {}
        root = raw.get("root_motion") or {}
        anim = raw.get("animation_sequence") or {}
        imp = raw.get("import") or {}
        chaos = raw.get("chaos_physics_ready") or {}
        return cls(
            name=str(raw.get("name", cfg_path.stem)),
            source_coordinate_system=str(raw.get("source_coordinate_system", "lab")),
            target_coordinate_system=str(raw.get("target_coordinate_system", "unreal")),
            unit_scale=UnitScale(
                source=str(unit.get("from", "Unknown")),
                target=str(unit.get("to", "cm")),
                factor=float(unit.get("factor", 0.1)),
                note=str(unit.get("note", "")),
            ),
            axes=AxisRemap(
                x=str(remap.get("x", "+x")),
                y=str(remap.get("y", "-y")),
                z=str(remap.get("z", "+z")),
                source_handedness=str(axes.get("source_handedness", "right")),
                target_handedness=str(axes.get("target_handedness", "left")),
                source_up=str(axes.get("source_up", "Z")),
                target_up=str(axes.get("target_up", "Z")),
            ),
            root_motion_enabled=bool(root.get("enable", True)),
            root_joint=str(root.get("root_joint", "Pelvis")),
            content_path=str(imp.get("content_path", "/Game/MotionEngine")),
            asset_prefix=str(imp.get("asset_prefix", "ME_")),
            skeleton_suffix=str(imp.get("skeleton_asset_suffix", "_Skeleton")),
            anim_suffix=str(imp.get("anim_asset_suffix", "_Anim")),
            enable_root_motion=bool(anim.get("enable_root_motion", True)),
            interpolation=str(anim.get("interpolation", "linear")),
            expose_sockets=list(chaos.get("expose_sockets") or []),
            raw=raw,
        )
