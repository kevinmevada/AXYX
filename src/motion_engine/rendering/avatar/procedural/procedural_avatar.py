"""Default metallic stick-figure avatar (current AXYX production look)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Sequence

import numpy as np
from numpy.typing import NDArray

from motion_engine.colors import ColorRGB
from motion_engine.rendering.avatar.avatar import Avatar

logger = logging.getLogger(__name__)

FloatArray = NDArray[np.floating]


@dataclass(slots=True)
class ProceduralPoseFrame:
    """Per-frame draw payload for the procedural metallic skeleton."""

    joint_positions: list[FloatArray] = field(default_factory=list)
    joint_radii: list[float] = field(default_factory=list)
    joint_colors: list[ColorRGB] = field(default_factory=list)
    bone_segments: list[tuple[FloatArray, FloatArray]] = field(default_factory=list)
    bone_colors: list[ColorRGB] = field(default_factory=list)
    bone_names: list[str] = field(default_factory=list)


class ProceduralAvatar(Avatar):
    """Graphite metallic bones + red glossy joints — default AXYX avatar.

    Mesh construction remains in ``PyVistaRenderer`` for Phase-0 compatibility.
    This class owns the *identity* and frame payload so future MetaHuman /
    SMPL avatars can swap in without Viewer changes.
    """

    DEFAULT_NAME: str = "procedural"

    def __init__(self, name: str = DEFAULT_NAME) -> None:
        super().__init__(name=name)
        self._frame = ProceduralPoseFrame()

    @property
    def frame(self) -> ProceduralPoseFrame:
        """Latest pose payload queued for rendering."""
        return self._frame

    def load(self, **kwargs: Any) -> None:
        """Mark the procedural avatar ready (no external assets required)."""
        _ = kwargs
        self._loaded = True
        logger.info("ProceduralAvatar loaded (metallic skeleton)")

    def update(self, frame: Any) -> None:
        """Accept a :class:`ProceduralPoseFrame` or mapping-like payload."""
        if isinstance(frame, ProceduralPoseFrame):
            self._frame = frame
            return
        if frame is None:
            self._frame = ProceduralPoseFrame()
            return
        # Allow duck-typed payloads from experimental callers.
        self._frame = ProceduralPoseFrame(
            joint_positions=list(getattr(frame, "joint_positions", [])),
            joint_radii=list(getattr(frame, "joint_radii", [])),
            joint_colors=list(getattr(frame, "joint_colors", [])),
            bone_segments=list(getattr(frame, "bone_segments", [])),
            bone_colors=list(getattr(frame, "bone_colors", [])),
            bone_names=list(getattr(frame, "bone_names", [])),
        )

    def render(self, backend: Any) -> None:
        """Delegate mesh flush to the PyVista backend when available."""
        flush = getattr(backend, "flush_procedural_avatar", None)
        if callable(flush):
            flush(self._frame)
            return
        logger.debug(
            "Backend %s has no flush_procedural_avatar; skipping",
            type(backend).__name__,
        )

    def clear_frame(self) -> None:
        """Reset the queued pose."""
        self._frame = ProceduralPoseFrame()


__all__ = ["ProceduralAvatar", "ProceduralPoseFrame"]
