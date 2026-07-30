"""Tests for theme mode selection."""

from __future__ import annotations

from motion_engine.studio.theme import (
    DARK_THEME,
    DEFAULT_THEME,
    HIGH_CONTRAST_THEME,
    get_theme,
)


def test_get_theme_modes() -> None:
    assert get_theme("light").mode == "light"
    assert get_theme("dark").mode == "dark"
    assert get_theme("night").mode == "dark"
    assert get_theme("high_contrast").mode == "high_contrast"
    assert get_theme("high-contrast").mode == "high_contrast"
    assert get_theme() is DEFAULT_THEME
    assert get_theme("dark") is DARK_THEME
    assert get_theme("high_contrast") is HIGH_CONTRAST_THEME
    assert get_theme("high_contrast").colors.accent == "#FFD600"
