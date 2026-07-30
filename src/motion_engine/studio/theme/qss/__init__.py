"""QSS assembly — load modular stylesheets and inject theme tokens."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from motion_engine.studio.theme.theme import StudioTheme

_QSS_DIR = Path(__file__).resolve().parent
_QSS_ORDER = (
    "base.qss",
    "dock.qss",
    "viewport.qss",
    "buttons.qss",
    "inputs.qss",
    "tables.qss",
    "tree.qss",
    "menus.qss",
    "dialogs.qss",
    "status.qss",
)


class _SafeTokenDict(dict[str, str]):
    """Return ``{token}`` unchanged when a placeholder is not in the map."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def token_map(theme: StudioTheme) -> dict[str, str]:
    """Flatten a :class:`StudioTheme` into QSS placeholder keys."""
    c = theme.colors
    t = theme.typography
    r = theme.radii
    s = theme.spacing
    color_fields = (
        "background",
        "surface",
        "surface_raised",
        "surface_sunken",
        "surface_overlay",
        "glass",
        "glass_strong",
        "glass_subtle",
        "glass_border",
        "glass_edge",
        "control",
        "border",
        "border_subtle",
        "border_strong",
        "highlight",
        "shadow_soft",
        "text_primary",
        "text_secondary",
        "text_muted",
        "text_disabled",
        "text_on_accent",
        "accent",
        "accent_hover",
        "accent_pressed",
        "accent_glow",
        "cyan",
        "selection_fill",
        "accent_muted",
        "accent_border",
        "success",
        "success_muted",
        "warning",
        "warning_muted",
        "danger",
        "danger_muted",
        "focus_ring",
        "shadow",
        "overlay_scrim",
        "viewport_void",
        "gradient_top",
        "gradient_mid",
        "gradient_bottom",
    )
    tokens: dict[str, str] = {name: getattr(c, name) for name in color_fields}
    tokens.update(
        {
            "font_family": t.family,
            "font_family_mono": t.family_mono,
            "size_xs": str(t.size_xs),
            "size_sm": str(t.size_sm),
            "size_md": str(t.size_md),
            "size_lg": str(t.size_lg),
            "size_xl": str(t.size_xl),
            "size_xxl": str(t.size_xxl),
            "size_display": str(t.size_display),
            "tracking_tight": t.tracking_tight,
            "tracking_wide": t.tracking_wide,
            "tracking_caps": t.tracking_caps,
            "radius_sm": str(r.sm),
            "radius_md": str(r.md),
            "radius_lg": str(r.lg),
            "radius_xl": str(r.xl),
            "radius_pill": str(r.pill),
            "space_xxs": str(s.xxs),
            "space_xs": str(s.xs),
            "space_sm": str(s.sm),
            "space_md": str(s.md),
            "space_lg": str(s.lg),
            "space_xl": str(s.xl),
            "space_xxl": str(s.xxl),
            "space_xxxl": str(s.xxxl),
        }
    )
    return tokens


def _load_qss(name: str) -> str:
    path = _QSS_DIR / name
    return path.read_text(encoding="utf-8")


def assemble_stylesheet(theme: StudioTheme) -> str:
    """Concatenate QSS modules and substitute token placeholders."""
    tokens = _SafeTokenDict(token_map(theme))
    parts: list[str] = []
    for name in _QSS_ORDER:
        raw = _load_qss(name)
        parts.append(raw.format_map(tokens))
    return "\n".join(parts)
