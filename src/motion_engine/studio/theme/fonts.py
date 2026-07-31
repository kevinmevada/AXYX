"""Studio font registration — Inter UI + Source Serif 4 display."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)
_REPO_ROOT = Path(__file__).resolve().parents[4]
_STUDIO_ASSETS = Path(__file__).resolve().parents[1] / "assets"
_REGISTERED = False
_INTER_FAMILY = "Inter"
_DISPLAY_FAMILY = "Source Serif 4"


def _font_search_roots() -> tuple[Path, ...]:
    return (
        _REPO_ROOT / "assets" / "fonts",
        _STUDIO_ASSETS / "fonts",
    )


def _register_file(path: Path, *, slot: str) -> None:
    if not path.is_file():
        return
    font_id = QFontDatabase.addApplicationFont(str(path))
    if font_id < 0:
        logger.warning("Failed to register font: %s", path)
        return
    families = QFontDatabase.applicationFontFamilies(font_id)
    if not families:
        return
    global _INTER_FAMILY, _DISPLAY_FAMILY
    if slot == "inter":
        _INTER_FAMILY = families[0]
    elif slot == "display":
        _DISPLAY_FAMILY = families[0]
    logger.debug("Registered font %s -> %s", path.name, families)


def register_studio_fonts() -> None:
    """Load Inter Variable (UI) and Source Serif 4 (wordmark) when assets are present."""
    global _REGISTERED
    if _REGISTERED:
        return
    for root in _font_search_roots():
        _register_file(root / "inter" / "InterVariable.ttf", slot="inter")
        _register_file(root / "inter" / "InterVariable-Italic.ttf", slot="inter")
        _register_file(
            root / "source-serif-4" / "SourceSerif4Variable.ttf", slot="display"
        )
    _REGISTERED = True


def studio_font_family() -> str:
    """Return the registered Inter family name (or last known fallback)."""
    register_studio_fonts()
    return _INTER_FAMILY


def studio_display_font_family() -> str:
    """Return Source Serif 4 when bundled, else a system serif, else Inter."""
    register_studio_fonts()
    if _DISPLAY_FAMILY in QFontDatabase.families():
        return _DISPLAY_FAMILY
    for fallback in (
        "Source Serif 4",
        "Source Serif Pro",
        "Georgia",
        "Times New Roman",
        "Palatino Linotype",
    ):
        if fallback in QFontDatabase.families():
            return fallback
    return studio_font_family()


def apply_app_font(app: QApplication, *, point_size: int = 14) -> None:
    """Set the global UI font — Inter when bundled, else system sans."""
    register_studio_fonts()
    family = studio_font_family()
    if family not in QFontDatabase.families():
        for fallback in (
            "Inter",
            "SF Pro Text",
            "Segoe UI Variable Text",
            "Segoe UI",
            "Liberation Sans",
        ):
            if fallback in QFontDatabase.families():
                family = fallback
                break
    font = QFont(family)
    font.setPointSize(point_size)
    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    app.setFont(font)
