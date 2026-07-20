"""Metallic procedural human — preserved fallback avatar."""

from __future__ import annotations

from typing import Any

from motion_engine.avatar.base import AvatarBackend
from motion_engine.skeleton import Pose, Skeleton


class MetallicAvatar(AvatarBackend):
    """Original gold/black PBR stick-figure.

    Does not draw itself — :class:`SkeletonViewer` continues to issue
    ``draw_sphere`` / ``draw_line`` calls when this backend is active.
    """

    id = "metallic"
    draws_procedural_skeleton = True

    def attach(self, renderer: Any) -> None:
        self._renderer = renderer

    def load(self, skeleton: Skeleton) -> None:
        return None

    def update(self, pose: Pose, *, skeleton: Skeleton) -> None:
        return None

    def clear(self) -> None:
        return None
