"""
HUD / overlay models for the Visualization Engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from motion_engine.colors import ColorRGB, DEFAULT_THEME


@dataclass(slots=True)
class HudState:
    """Heads-up display content for one frame."""

    frame_number: int = 0
    n_frames: int = 0
    current_time_seconds: float = 0.0
    fps: float = 0.0
    playback_speed: float = 1.0
    subject_id: str = ""
    session_name: str = ""
    joint_count: int = 0
    bone_count: int = 0
    coordinate_system: str = "lab"
    playing: bool = False
    extra_lines: list[str] = field(default_factory=list)


@dataclass(slots=True)
class OverlayStyle:
    """Visual style for HUD text / panels."""

    text_color: ColorRGB = DEFAULT_THEME.hud_text
    panel_alpha: float = 0.55
    font_size: int = 11


class OverlayRenderer:
    """Backend-agnostic overlay contract.

    TODO: Concrete Open3D / Matplotlib HUD painters.
    """

    def draw(self, hud: HudState, style: OverlayStyle | None = None) -> None:
        """Draw HUD overlays into the active renderer surface."""
        raise NotImplementedError("OverlayRenderer.draw is backend-specific.")
