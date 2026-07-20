"""Resource path helpers for AXYX assets."""

from __future__ import annotations

from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent
ASSETS_ROOT = PACKAGE_ROOT / "assets"
STYLES_ROOT = ASSETS_ROOT / "styles"
ICONS_ROOT = ASSETS_ROOT / "icons"
FONTS_ROOT = ASSETS_ROOT / "fonts"


def asset_path(*parts: str) -> Path:
    """Join paths under the studio assets root."""
    return ASSETS_ROOT.joinpath(*parts)


def ensure_asset_dirs() -> None:
    """Create asset directories if missing."""
    for path in (ASSETS_ROOT, STYLES_ROOT, ICONS_ROOT, FONTS_ROOT):
        path.mkdir(parents=True, exist_ok=True)
