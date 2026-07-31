"""Visualization mode identifiers for the premium rendering framework."""

from __future__ import annotations

from enum import Enum


class VisualizationMode(str, Enum):
    """Interchangeable visualization backends (playback-agnostic)."""

    STICK = "stick"
    BONES = "bones"
    AVATAR = "avatar"

    @classmethod
    def parse(cls, value: str | VisualizationMode) -> VisualizationMode:
        if isinstance(value, VisualizationMode):
            return value
        key = str(value).strip().lower()
        aliases = {
            "stick": cls.STICK,
            "stick_figure": cls.STICK,
            "clinical": cls.STICK,
            "bones": cls.BONES,
            "bone": cls.BONES,
            "anatomy": cls.BONES,
            "anatomical": cls.BONES,
            "skeleton": cls.BONES,
            "avatar": cls.AVATAR,
            "human": cls.AVATAR,
            "digital_twin": cls.AVATAR,
            "twin": cls.AVATAR,
        }
        if key not in aliases:
            raise ValueError(f"Unknown visualization mode: {value!r}")
        return aliases[key]
