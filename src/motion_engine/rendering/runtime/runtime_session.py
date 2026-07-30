"""Research session — subject / trial / avatar / mapping selections."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from motion_engine.rendering.runtime.runtime_configuration import RuntimeConfiguration
from motion_engine.rendering.runtime.types import AvatarKind, PlaybackMode, RuntimeReport


@dataclass
class RuntimeSession:
    """One research session spanning database selection through playback."""

    subject_id: str | None = None
    trial_id: str | None = None  # MotionDatabase session name
    avatar_kind: AvatarKind = AvatarKind.FIXTURE
    avatar_name: str = "fixture"
    mapping_profile: str = "test_two_bone"
    playback_mode: PlaybackMode = PlaybackMode.RETARGET
    config: RuntimeConfiguration = field(default_factory=RuntimeConfiguration)
    statistics: RuntimeReport = field(default_factory=RuntimeReport)
    metadata: dict[str, Any] = field(default_factory=dict)
    frame_index: int = 0
    time_sec: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "trial_id": self.trial_id,
            "avatar_kind": self.avatar_kind.value,
            "avatar_name": self.avatar_name,
            "mapping_profile": self.mapping_profile,
            "playback_mode": self.playback_mode.value,
            "frame_index": self.frame_index,
            "time_sec": self.time_sec,
            "statistics": self.statistics.as_dict(),
            "metadata": dict(self.metadata),
        }


__all__ = ["RuntimeSession"]
