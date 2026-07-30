"""Runtime configuration + presets (JSON import/export)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from motion_engine.rendering.runtime.constants import (
    DEFAULT_AVATAR,
    DEFAULT_FPS,
    DEFAULT_MAPPING_PROFILE,
    PRESET_BENCHMARK,
    PRESET_DEBUG,
    PRESET_DEFAULT,
    PRESET_RESEARCH,
    SCHEMA_VERSION,
)
from motion_engine.rendering.runtime.exceptions import RuntimeConfigError
from motion_engine.rendering.runtime.types import AvatarKind, PlaybackMode


@dataclass
class RuntimeConfiguration:
    """Tunable digital-twin runtime settings."""

    name: str = PRESET_DEFAULT
    fps: float = DEFAULT_FPS
    avatar: str = DEFAULT_AVATAR
    mapping_profile: str = DEFAULT_MAPPING_PROFILE
    playback_mode: str = PlaybackMode.RETARGET.value
    root_motion: str = "world"
    mirror: bool = False
    synthetic_frames: int = 60
    enable_profiler: bool = True
    enable_cache: bool = True
    validate_each_frame: bool = False
    log_level: str = "INFO"
    database_path: str | None = None
    subject_id: str | None = None
    trial_id: str | None = None  # Session name in MotionDatabase terms
    army_girl_fbx: str | None = None
    metahuman_lod: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)

    def avatar_kind(self) -> AvatarKind:
        try:
            return AvatarKind(self.avatar)
        except ValueError:
            return AvatarKind.CUSTOM

    def playback(self) -> PlaybackMode:
        return PlaybackMode(self.playback_mode)

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema_version"] = SCHEMA_VERSION
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuntimeConfiguration:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        return cls(**kwargs)


def preset_default() -> RuntimeConfiguration:
    return RuntimeConfiguration(name=PRESET_DEFAULT)


def preset_research() -> RuntimeConfiguration:
    return RuntimeConfiguration(
        name=PRESET_RESEARCH,
        fps=100.0,
        avatar=AvatarKind.ARMY_GIRL.value,
        mapping_profile="matlab_clinical_to_army_girl",
        validate_each_frame=True,
        enable_profiler=True,
        synthetic_frames=120,
    )


def preset_debug() -> RuntimeConfiguration:
    return RuntimeConfiguration(
        name=PRESET_DEBUG,
        fps=30.0,
        avatar=AvatarKind.FIXTURE.value,
        mapping_profile="test_two_bone",
        validate_each_frame=True,
        log_level="DEBUG",
        synthetic_frames=30,
    )


def preset_benchmark() -> RuntimeConfiguration:
    return RuntimeConfiguration(
        name=PRESET_BENCHMARK,
        fps=30.0,
        avatar=AvatarKind.FIXTURE.value,
        mapping_profile="test_two_bone",
        enable_profiler=True,
        validate_each_frame=False,
        synthetic_frames=1000,
    )


PRESETS = {
    PRESET_DEFAULT: preset_default,
    PRESET_RESEARCH: preset_research,
    PRESET_DEBUG: preset_debug,
    PRESET_BENCHMARK: preset_benchmark,
}


def load_configuration(path: str | Path) -> RuntimeConfiguration:
    path = Path(path)
    if not path.is_file():
        raise RuntimeConfigError(f"Config not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return RuntimeConfiguration.from_dict(data)


def save_configuration(cfg: RuntimeConfiguration, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg.as_dict(), indent=2), encoding="utf-8")


def get_preset(name: str) -> RuntimeConfiguration:
    if name not in PRESETS:
        raise RuntimeConfigError(f"Unknown preset: {name}")
    return PRESETS[name]()


__all__ = [
    "RuntimeConfiguration",
    "preset_default",
    "preset_research",
    "preset_debug",
    "preset_benchmark",
    "PRESETS",
    "load_configuration",
    "save_configuration",
    "get_preset",
]
