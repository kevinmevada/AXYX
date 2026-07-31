"""Apply a light Fusion palette so transparent dock holes stay Museum White."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from motion_engine.studio.theme.theme import StudioTheme


def apply_museum_palette(app: QApplication, theme: StudioTheme) -> None:
    """Force Fusion Window/Base colors to theme tokens (fixes dark dock bleed)."""
    c = theme.colors
    palette = QPalette(app.palette())
    bg = QColor(c.background)
    surface = QColor(c.surface)
    text = QColor(c.text_primary)
    secondary = QColor(c.text_secondary)
    disabled = QColor(c.text_disabled)
    accent = QColor(c.accent)
    highlight = QColor(c.selection_fill)
    muted = QColor(c.text_muted)

    palette.setColor(QPalette.ColorRole.Window, bg)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, surface)
    palette.setColor(QPalette.ColorRole.AlternateBase, bg)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, bg)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.BrightText, text)
    palette.setColor(QPalette.ColorRole.ToolTipBase, surface)
    palette.setColor(QPalette.ColorRole.ToolTipText, text)
    # Placeholder tuned for Museum White surfaces (not dark-void contrast).
    palette.setColor(QPalette.ColorRole.PlaceholderText, muted)
    # Selection = pale violet tint + ink text (never accent fill + white).
    palette.setColor(QPalette.ColorRole.Highlight, highlight)
    palette.setColor(QPalette.ColorRole.HighlightedText, text)
    palette.setColor(QPalette.ColorRole.Link, accent)
    palette.setColor(QPalette.ColorRole.Light, surface)
    palette.setColor(QPalette.ColorRole.Midlight, highlight)
    palette.setColor(QPalette.ColorRole.Mid, QColor(c.border_strong))
    palette.setColor(QPalette.ColorRole.Dark, secondary)
    palette.setColor(QPalette.ColorRole.Shadow, QColor(c.border))

    for group in (
        QPalette.ColorGroup.Active,
        QPalette.ColorGroup.Inactive,
        QPalette.ColorGroup.Disabled,
    ):
        palette.setColor(group, QPalette.ColorRole.Window, bg)
        palette.setColor(group, QPalette.ColorRole.Base, surface)
        palette.setColor(group, QPalette.ColorRole.Button, bg)
        if group == QPalette.ColorGroup.Disabled:
            palette.setColor(group, QPalette.ColorRole.WindowText, disabled)
            palette.setColor(group, QPalette.ColorRole.Text, disabled)
            palette.setColor(group, QPalette.ColorRole.ButtonText, disabled)
        else:
            palette.setColor(group, QPalette.ColorRole.WindowText, text)
            palette.setColor(group, QPalette.ColorRole.Text, text)
            palette.setColor(group, QPalette.ColorRole.ButtonText, text)

    app.setPalette(palette)
