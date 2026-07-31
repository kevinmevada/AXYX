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


# AXYX Museum White — Graphite Ink bones; glow joints (purple body, red head).
_WHITE: ColorRGB = _hex("FFFFFF")
_GRAPHITE: ColorRGB = _hex("1C1E1C")
_GRAPHITE_SOFT: ColorRGB = _hex("6E6E6B")
# Glow joint regions — purple body, red head (viewport only).
JOINT_HEAD: ColorRGB = _hex("FF6B63")
JOINT_BODY: ColorRGB = _hex("C4A8FF")


def joint_region_color(joint_name: str, default: ColorRGB | None = None) -> ColorRGB:
    """Display color by region — head red, everything else purple."""
    key = joint_name.lower()
    if "head" in key or "skull" in key:
        return JOINT_HEAD
    return default if default is not None else JOINT_BODY


STUDIO_THEME: Final[Theme] = Theme(
    name="studio",
    background=_WHITE,
    background_top=_WHITE,
    ground=_WHITE,
    grid=_GRAPHITE_SOFT,
    grid_minor=_GRAPHITE_SOFT,
    bone=_GRAPHITE,
    bone_highlight=_GRAPHITE_SOFT,
    joint=JOINT_BODY,
    joint_highlight=_hex("DCCBFF"),
    label=_GRAPHITE,
    axis_x=JOINT_BODY,
    axis_y=_GRAPHITE_SOFT,
    axis_z=_GRAPHITE_SOFT,
    hud_text=_GRAPHITE_SOFT,
    selected=_hex("DCCBFF"),
    floor_accent=_WHITE,
    fog=_WHITE,
)

# Legacy Flagship dark void (opt-in via get_theme("dark")).
DARK_THEME: Final[Theme] = Theme(
    name="dark",
    background=_hex("0B090D"),
    background_top=_hex("161311"),
    ground=_hex("0B090D"),
    grid=_hex("A29D94"),
    grid_minor=_hex("78766E"),
    bone=_hex("D0AC68"),
    bone_highlight=_hex("DEC28C"),
    joint=_hex("F4E8D0"),
    joint_highlight=_hex("F8F0E4"),
    label=_hex("F1EEE8"),
    axis_x=_hex("D0AC68"),
    axis_y=_hex("A29D94"),
    axis_z=_hex("78623A"),
    hud_text=_hex("F1EEE8"),
    selected=_hex("DEC28C"),
    floor_accent=_hex("1A1714"),
    fog=_hex("0B090D"),
)

# Legacy light photography look (opt-in via get_theme("light")).
LIGHT_THEME: Final[Theme] = Theme(
    name="light",
    background=_hex("EEEEEF"),
    background_top=_hex("F7F7F8"),
    ground=_hex("F4F4F6"),
    grid=_hex("C8CAD0"),
    grid_minor=_hex("D8DAE0"),
    bone=_hex("3A3D42"),
    bone_highlight=_hex("55585E"),
    joint=_hex("E8443A"),
    joint_highlight=_hex("FF6B5E"),
    label=_hex("2C2E32"),
    axis_x=_hex("E8443A"),
    axis_y=_hex("8A8E96"),
    axis_z=_hex("4F8CFF"),
    hud_text=_hex("2C2E32"),
    selected=_hex("4F8CFF"),
    floor_accent=_hex("E6E7EA"),
    fog=_hex("EEEEEF"),
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
