"""Avatar backend protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from motion_engine.skeleton import Pose, Skeleton


@dataclass(slots=True)
class AvatarInfo:
    """Registry metadata for one swappable avatar."""

    id: str
    display_name: str
    backend: str
    enabled: bool = True
    fallback: bool = False
    asset_root: str | None = None
    manifest: str | None = None
    retarget: str | None = None
    default_lod: int = 1
    animation_mode: str = "rigid"
    description: str = ""


class AvatarBackend(ABC):
    """Draw / update one character representation from Motion Engine poses."""

    id: str = "base"
    draws_procedural_skeleton: bool = False

    @abstractmethod
    def attach(self, renderer: Any) -> None:
        """Bind to a concrete renderer (usually PyVistaRenderer)."""

    @abstractmethod
    def load(self, skeleton: Skeleton) -> None:
        """Prepare avatar for a newly selected skeleton/session."""

    @abstractmethod
    def update(self, pose: Pose, *, skeleton: Skeleton) -> None:
        """Apply one frame of motion."""

    @abstractmethod
    def clear(self) -> None:
        """Remove avatar drawables from the scene."""

    def set_visible(self, visible: bool) -> None:
        """Optional visibility toggle."""

    def set_lod(self, lod: int) -> None:
        """Optional LOD switch."""


class NullAvatar(AvatarBackend):
    """No-op backend used in headless tests."""

    id = "null"
    draws_procedural_skeleton = True

    def attach(self, renderer: Any) -> None:
        return None

    def load(self, skeleton: Skeleton) -> None:
        return None

    def update(self, pose: Pose, *, skeleton: Skeleton) -> None:
        return None

    def clear(self) -> None:
        return None
