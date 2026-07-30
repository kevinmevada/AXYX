"""Inter Variable font registration for Motion Studio."""
from __future__ import annotations
import logging
from pathlib import Path
from PySide6.QtGui import QFontDatabase
logger = logging.getLogger(__name__)
_REPO_ROOT = Path(__file__).resolve().parents[4]
_STUDIO_ASSETS = Path(__file__).resolve().parents[1] / "assets"
_REGISTERED = False

def _font_search_roots() -> tuple[Path, ...]:
    return (
        _REPO_ROOT / "assets" / "fonts" / "inter",
        _STUDIO_ASSETS / "fonts" / "inter",
    )

def _register_file(path: Path) -> None:
    if not path.is_file():
        return
    font_id = QFontDatabase.addApplicationFont(str(path))
    if font_id < 0:
        logger.warning("Failed to register font: %s", path)
        return
    families = QFontDatabase.applicationFontFamilies(font_id)
    logger.debug("Registered font %s -> %s", path.name, families)

def register_studio_fonts() -> None:
    """Load Inter Variable (regular + italic) when assets are present."""
    global _REGISTERED
    if _REGISTERED:
        return
    for root in _font_search_roots():
        _register_file(root / "InterVariable.ttf")
        _register_file(root / "InterVariable-Italic.ttf")
    _REGISTERED = True
