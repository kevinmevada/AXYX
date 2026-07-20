"""
Centralized color management for the Visualization Engine.

Never hardcode RGB literals in viewer/renderer code - import from here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


ColorRGB = tuple[float, float, float]
"""RGB in 0-1 floating range (renderer-neutral)."""


def _hex(value: str) -> ColorRGB:
    """Convert ``#RRGGBB`` to linear-ish 0-1 RGB for VTK."""
    value = value.lstrip("#")
    r = int(value[0:2], 16) / 255.0
    g = int(value[2:4], 16) / 255.0
    b = int(value[4:6], 16) / 255.0
    return (r, g, b)


@dataclass(frozen=True, slots=True)
class Theme:
    """Named visual theme for the Visualization Engine."""

    name: str
    background: ColorRGB
    background_top: ColorRGB
    ground: ColorRGB
    grid: ColorRGB
    grid_minor: ColorRGB
    joint: ColorRGB
    bone: ColorRGB
    joint_highlight: ColorRGB
    bone_highlight: ColorRGB
    label: ColorRGB
    axis_x: ColorRGB
    axis_y: ColorRGB
    axis_z: ColorRGB
    hud_text: ColorRGB
    selected: ColorRGB
    floor_accent: ColorRGB
    fog: ColorRGB


# Light photography studio — pale floor, graphite bones, red joint accents.
_FLOOR: ColorRGB = _hex("F4F4F6")
_FLOOR_WARM: ColorRGB = _hex("E6E7EA")
_WALL: ColorRGB = _hex("EEEEEF")
_GRAPHITE: ColorRGB = _hex("3A3D42")
_GRAPHITE_HI: ColorRGB = _hex("55585E")
_JOINT_RED: ColorRGB = _hex("E8443A")
_GRID: ColorRGB = _hex("C8CAD0")
_GRID_MINOR: ColorRGB = _hex("D8DAE0")
_ACCENT: ColorRGB = _hex("4F8CFF")
_INK: ColorRGB = _hex("2C2E32")

STUDIO_THEME: Final[Theme] = Theme(
    name="studio",
    background=_WALL,
    background_top=_hex("F7F7F8"),
    ground=_FLOOR,
    grid=_GRID,
    grid_minor=_GRID_MINOR,
    bone=_GRAPHITE,
    bone_highlight=_GRAPHITE_HI,
    joint=_JOINT_RED,
    joint_highlight=_hex("FF6B5E"),
    label=_INK,
    axis_x=_JOINT_RED,
    axis_y=_hex("8A8E96"),
    axis_z=_ACCENT,
    hud_text=_INK,
    selected=_ACCENT,
    floor_accent=_FLOOR_WARM,
    fog=_WALL,
)

DARK_THEME: Final[Theme] = Theme(
    name="dark",
    background=(0.08, 0.09, 0.11),
    background_top=(0.04, 0.05, 0.06),
    ground=(0.16, 0.17, 0.20),
    grid=(0.28, 0.30, 0.34),
    grid_minor=(0.20, 0.22, 0.25),
    joint=(0.55, 0.13, 0.22),
    bone=(0.75, 0.80, 0.88),
    joint_highlight=(0.72, 0.19, 0.30),
    bone_highlight=(0.90, 0.92, 0.95),
    label=(0.90, 0.92, 0.95),
    axis_x=(0.90, 0.25, 0.25),
    axis_y=(0.30, 0.85, 0.35),
    axis_z=(0.30, 0.55, 0.95),
    hud_text=(0.92, 0.93, 0.95),
    selected=(0.31, 0.55, 1.00),
    floor_accent=(0.20, 0.21, 0.24),
    fog=(0.08, 0.09, 0.11),
)

LIGHT_THEME: Final[Theme] = Theme(
    name="light",
    background=(0.88, 0.89, 0.91),
    background_top=(0.96, 0.96, 0.97),
    ground=(0.82, 0.83, 0.85),
    grid=(0.65, 0.67, 0.70),
    grid_minor=(0.74, 0.76, 0.78),
    joint=(0.55, 0.13, 0.22),
    bone=(0.30, 0.34, 0.40),
    joint_highlight=(0.72, 0.19, 0.30),
    bone_highlight=(0.10, 0.45, 0.90),
    label=(0.12, 0.12, 0.14),
    axis_x=(0.85, 0.15, 0.15),
    axis_y=(0.15, 0.65, 0.25),
    axis_z=(0.15, 0.35, 0.85),
    hud_text=(0.12, 0.12, 0.14),
    selected=(0.31, 0.55, 1.00),
    floor_accent=(0.76, 0.77, 0.79),
    fog=(0.90, 0.91, 0.92),
)

CLINICAL_THEME: Final[Theme] = Theme(
    name="clinical",
    background=(0.90, 0.93, 0.95),
    background_top=(0.95, 0.97, 0.98),
    ground=(0.86, 0.90, 0.92),
    grid=(0.68, 0.76, 0.80),
    grid_minor=(0.78, 0.84, 0.87),
    joint=(0.10, 0.45, 0.70),
    bone=(0.22, 0.36, 0.48),
    joint_highlight=(0.85, 0.20, 0.20),
    bone_highlight=(0.05, 0.60, 0.55),
    label=(0.12, 0.16, 0.20),
    axis_x=(0.80, 0.20, 0.20),
    axis_y=(0.20, 0.65, 0.30),
    axis_z=(0.20, 0.40, 0.80),
    hud_text=(0.12, 0.16, 0.20),
    selected=(0.95, 0.50, 0.10),
    floor_accent=(0.80, 0.85, 0.88),
    fog=(0.92, 0.94, 0.96),
)

PUBLICATION_THEME: Final[Theme] = Theme(
    name="publication",
    background=(0.94, 0.94, 0.94),
    background_top=(1.00, 1.00, 1.00),
    ground=(0.90, 0.90, 0.90),
    grid=(0.72, 0.72, 0.72),
    grid_minor=(0.82, 0.82, 0.82),
    joint=(0.05, 0.05, 0.05),
    bone=(0.25, 0.25, 0.25),
    joint_highlight=(0.55, 0.00, 0.00),
    bone_highlight=(0.00, 0.00, 0.55),
    label=(0.00, 0.00, 0.00),
    axis_x=(0.70, 0.00, 0.00),
    axis_y=(0.00, 0.55, 0.00),
    axis_z=(0.00, 0.00, 0.70),
    hud_text=(0.00, 0.00, 0.00),
    selected=(0.00, 0.00, 0.00),
    floor_accent=(0.88, 0.88, 0.88),
    fog=(0.96, 0.96, 0.96),
)

DEFAULT_THEME: Final[Theme] = STUDIO_THEME

THEMES: Final[dict[str, Theme]] = {
    STUDIO_THEME.name: STUDIO_THEME,
    DARK_THEME.name: DARK_THEME,
    LIGHT_THEME.name: LIGHT_THEME,
    CLINICAL_THEME.name: CLINICAL_THEME,
    PUBLICATION_THEME.name: PUBLICATION_THEME,
}


def get_theme(name: str = "studio") -> Theme:
    """Return a registered theme by name."""
    try:
        return THEMES[name]
    except KeyError as exc:
        raise KeyError(
            f"Unknown theme {name!r}. Available: {sorted(THEMES)}"
        ) from exc
