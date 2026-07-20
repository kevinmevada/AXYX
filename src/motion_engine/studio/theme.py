"""Premium soft UI theme - AXYX.

Visual language: Apple Pro Ã- Omniverse Ã- soft clay elevation.
Layered surfaces, soft floating shadows, accent #4F8CFF.
Not heavy neumorphism - subtle lift only.

Elevation (apply_elevation)
---------------------------
1 - Dock panels (sidebar, inspector) - soft float
2 - Cards / timeline / chrome chips
3 - Welcome / overlays

All colors / radii / spacing / fonts come from this module.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget


@dataclass(frozen=True, slots=True)
class StudioColors:
    """Layered light surfaces + dark viewport + Apple-style accents."""

    background: str = "#ECECEC"
    surface: str = "#F5F5F7"
    surface_raised: str = "#FFFFFF"
    surface_sunken: str = "#E8E8ED"
    surface_overlay: str = "#F0F0F3"
    glass: str = "#F5F5F7"
    glass_border: str = "#E5E5EA"
    control: str = "#FCFCFC"

    border: str = "#E5E5EA"
    border_subtle: str = "#ECECEF"
    border_strong: str = "#D1D1D6"
    highlight: str = "#FFFFFF"
    shadow_soft: str = "#000000"

    text_primary: str = "#1D1D1F"
    text_secondary: str = "#1D1D1F"
    text_muted: str = "#1D1D1F"
    text_disabled: str = "#8E8E93"
    text_on_accent: str = "#FFFFFF"

    accent: str = "#4F8CFF"
    accent_hover: str = "#6BA0FF"
    accent_pressed: str = "#3A74E0"
    accent_glow: str = "#4F8CFF"
    cyan: str = "#5AC8F5"
    selection_fill: str = "#E8F0FF"
    accent_muted: str = "#E8F0FF"
    accent_border: str = "#B8D0FF"

    success: str = "#34C759"
    success_muted: str = "#E4F8EA"
    warning: str = "#FF9F0A"
    warning_muted: str = "#FFF3E0"
    danger: str = "#FF453A"
    danger_muted: str = "#FFE5E3"

    focus_ring: str = "#4F8CFF"
    shadow: str = "#000000"
    overlay_scrim: str = "#1D1D1F"
    viewport_void: str = "#1C2026"


@dataclass(frozen=True, slots=True)
class StudioSpacing:
    xxs: int = 2
    xs: int = 4
    sm: int = 8
    md: int = 16
    lg: int = 24
    xl: int = 32
    xxl: int = 40
    xxxl: int = 56


@dataclass(frozen=True, slots=True)
class StudioRadii:
    sm: int = 10
    md: int = 14  # buttons
    lg: int = 18  # cards
    xl: int = 20  # panels / viewport
    pill: int = 999


@dataclass(frozen=True, slots=True)
class StudioTypography:
    family: str = (
        "'Inter', 'SF Pro Text', 'Segoe UI Variable', 'Segoe UI', sans-serif"
    )
    family_mono: str = (
        "'SF Mono', 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace"
    )
    size_xs: int = 12   # values
    size_sm: int = 13   # labels
    size_md: int = 14
    size_lg: int = 15   # section headers
    size_xl: int = 18   # panel titles
    size_xxl: int = 22
    size_display: int = 28
    tracking_tight: str = "-0.3px"
    tracking_wide: str = "0.3px"
    tracking_caps: str = "0.8px"


@dataclass(frozen=True, slots=True)
class StudioIcons:
    xs: int = 16
    sm: int = 18
    md: int = 20
    lg: int = 28
    stroke: float = 1.5


@dataclass(frozen=True, slots=True)
class StudioMotion:
    instant: int = 80
    fast: int = 150
    base: int = 220
    slow: int = 340


@dataclass(frozen=True, slots=True)
class StudioTheme:
    colors: StudioColors = StudioColors()
    spacing: StudioSpacing = StudioSpacing()
    radii: StudioRadii = StudioRadii()
    typography: StudioTypography = StudioTypography()
    icons: StudioIcons = StudioIcons()
    motion: StudioMotion = StudioMotion()
    name: str = "human_motion_lab_premium"
    mode: str = "light"


# Soft float: ~0 8px 30px rgba(0,0,0,.08)
_ELEVATION_LEVELS: dict[int, tuple[int, int, int]] = {
    1: (30, 8, 20),
    2: (36, 10, 28),
    3: (48, 14, 36),
}


def apply_elevation(widget: QWidget, level: int = 1, *, color: str | None = None) -> None:
    """Soft floating shadow - never heavy clay extrusion."""
    blur, offset, alpha = _ELEVATION_LEVELS.get(level, _ELEVATION_LEVELS[1])
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, offset)
    q = QColor(color or DEFAULT_THEME.colors.shadow)
    q.setAlpha(alpha)
    effect.setColor(q)
    widget.setGraphicsEffect(effect)


def build_stylesheet(theme: StudioTheme | None = None) -> str:
    """Application-wide premium soft stylesheet."""
    theme = theme or StudioTheme()
    c = theme.colors
    t = theme.typography
    r = theme.radii
    s = theme.spacing
    return f"""
    * {{
        font-family: {t.family};
        font-size: {t.size_md}px;
        color: {c.text_primary};
        outline: none;
    }}
    QMainWindow, QDialog {{
        background-color: {c.background};
    }}
    QWidget {{
        background-color: transparent;
        color: {c.text_primary};
    }}
    QWidget#Workspace,
    QWidget#WelcomeRoot {{
        background-color: {c.background};
    }}
    QWidget#LoadingOverlay {{
        background-color: {c.overlay_scrim};
    }}
    QWidget#CommandBar {{
        background-color: {c.surface};
        border: none;
        border-bottom: 1px solid {c.border_subtle};
    }}
    QWidget#ViewportStage {{
        background-color: {c.viewport_void};
        border: none;
        border-radius: {r.xl}px;
    }}
    QWidget#TimelineDock {{
        background-color: {c.surface_raised};
        border: 1px solid {c.border_subtle};
        border-radius: {r.md}px;
    }}
    QWidget#ViewportToolbar {{
        background: rgba(255, 255, 255, 0.78);
        border: 1px solid {c.border_subtle};
        border-radius: {r.lg}px;
        padding: 4px 8px;
    }}
    QFrame#ToolbarDivider {{
        background-color: {c.border_subtle};
        max-width: 1px;
        min-width: 1px;
        margin: 6px 4px;
        border: none;
    }}

    QFrame#Sidebar,
    QFrame#InspectorPanel {{
        background-color: {c.surface};
        border: 1px solid {c.border_subtle};
        border-radius: {r.xl}px;
    }}
    QFrame#CenterPanel {{
        background-color: transparent;
        border: none;
    }}
    QFrame#Card,
    QFrame#InspectorCard {{
        background-color: {c.surface_raised};
        border: 1px solid {c.border_subtle};
        border-radius: {r.lg}px;
    }}
    QFrame#Divider {{
        background-color: {c.border_subtle};
        max-height: 1px;
        min-height: 1px;
        border: none;
    }}
    QFrame#ToolbarDivider {{
        background-color: {c.border};
        max-width: 1px;
        min-width: 1px;
        border: none;
        margin: {s.xs}px {s.sm}px;
    }}
    QFrame#ErrorBanner {{
        background-color: {c.danger_muted};
        border: 1px solid {c.danger};
        border-radius: {r.md}px;
    }}
    QFrame#EmptyState {{
        background: {c.surface_sunken};
        border: none;
        border-radius: {r.lg}px;
        min-height: 100px;
    }}
    QGroupBox {{
        background: {c.surface_raised};
        border: 1px solid {c.border_subtle};
        border-radius: {r.lg}px;
        margin-top: {s.md}px;
        padding: {s.md}px;
        font-weight: 600;
        color: {c.text_primary};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: {s.sm}px;
        padding: 0 {s.xs}px;
        color: {c.text_primary};
        font-size: {t.size_xs}px;
        letter-spacing: {t.tracking_caps};
        text-transform: uppercase;
    }}

    QLabel#BrandTitle {{
        font-size: {t.size_xl}px;
        font-weight: 700;
        letter-spacing: {t.tracking_tight};
        color: {c.text_primary};
    }}
    QLabel#BrandSubtitle,
    QLabel#MutedLabel {{
        color: {c.text_primary};
        font-size: {t.size_sm}px;
    }}
    QLabel#SectionLabel {{
        color: {c.text_primary};
        font-size: {t.size_lg}px;
        font-weight: 600;
        letter-spacing: {t.tracking_wide};
        padding-top: {s.xs}px;
    }}
    QLabel#HeroTitle {{
        font-size: {t.size_display}px;
        font-weight: 700;
        letter-spacing: {t.tracking_tight};
        color: {c.text_primary};
    }}
    QLabel#FeatureHeading {{
        font-weight: 600;
        font-size: {t.size_sm}px;
        color: {c.text_primary};
    }}
    QLabel#FeatureBody {{
        font-size: {t.size_xs}px;
        color: {c.text_primary};
    }}
    QLabel#MetricValue {{
        font-family: {t.family_mono};
        font-size: {t.size_xs}px;
        font-weight: 600;
        color: {c.text_primary};
    }}
    QLabel#EyebrowLabel {{
        color: {c.accent};
        font-size: {t.size_xs}px;
        font-weight: 700;
        letter-spacing: {t.tracking_caps};
        text-transform: uppercase;
    }}
    QLabel#ErrorBannerText {{
        color: {c.danger};
        font-size: {t.size_sm}px;
        font-weight: 600;
    }}
    QLabel#EmptyTitle {{
        font-size: {t.size_lg}px;
        font-weight: 650;
        color: {c.text_primary};
    }}
    QLabel#EmptySubtitle {{
        font-size: {t.size_sm}px;
        color: {c.text_primary};
    }}
    QLabel#TimecodeLabel {{
        font-family: {t.family_mono};
        font-size: {t.size_sm}px;
        color: {c.accent};
        letter-spacing: 0.4px;
    }}
    QLabel#FrameLabel {{
        font-family: {t.family_mono};
        font-size: {t.size_xs}px;
        color: {c.text_secondary};
    }}

    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background: {c.control};
        border: 1px solid {c.border};
        border-radius: {r.md}px;
        padding: 10px {s.md}px;
        selection-background-color: {c.accent};
        selection-color: {c.text_on_accent};
        color: {c.text_primary};
    }}
    QLineEdit:hover, QComboBox:hover {{
        border-color: {c.border_strong};
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 2px solid {c.focus_ring};
        background: {c.surface_raised};
        padding: 9px 15px;
    }}
    QLineEdit:disabled, QComboBox:disabled {{
        color: {c.text_disabled};
    }}
    QLineEdit#SearchField {{
        border-radius: {r.pill}px;
        background: {c.control};
        padding-left: {s.md}px;
    }}
    QComboBox#CompactSpeed {{
        min-height: 30px;
        max-height: 30px;
        padding: 2px 18px 2px 8px;
        font-family: {t.family_mono};
        font-size: {t.size_xs}px;
    }}
    QComboBox#CompactSpeed:focus {{
        padding: 1px 17px 1px 7px;
    }}
    QComboBox::drop-down {{
        border: none;
        width: {s.xl}px;
    }}
    QComboBox QAbstractItemView {{
        background: {c.surface_raised};
        border: 1px solid {c.border};
        border-radius: {r.md}px;
        selection-background-color: {c.selection_fill};
        selection-color: {c.accent_pressed};
        padding: {s.xs}px;
        outline: none;
    }}

    QAbstractItemView {{
        background: transparent;
        outline: none;
        show-decoration-selected: 1;
        selection-background-color: {c.selection_fill};
        selection-color: {c.accent_pressed};
    }}
    QListWidget, QTreeWidget, QTableWidget {{
        background: transparent;
        border: none;
        border-radius: {r.md}px;
        padding: {s.xs}px;
        outline: none;
        show-decoration-selected: 1;
        selection-background-color: {c.selection_fill};
        selection-color: {c.accent_pressed};
    }}
    QListWidget#StudioList,
    QListWidget#CohortList,
    QListWidget#RecentList,
    QListWidget#MetricsList,
    QListWidget#SessionList {{
        background: transparent;
        border: none;
    }}
    QListWidget::item, QTreeWidget::item, QTableWidget::item {{
        padding: 10px {s.md}px;
        border-radius: {r.md}px;
        margin: 2px 1px;
        color: {c.text_primary};
        background: transparent;
        border: 1px solid transparent;
    }}
    QListWidget::item:selected,
    QTreeWidget::item:selected,
    QTableWidget::item:selected,
    QListWidget::item:selected:!active,
    QTreeWidget::item:selected:!active,
    QTableWidget::item:selected:!active {{
        background: {c.selection_fill};
        color: {c.accent_pressed};
        border: 1px solid {c.accent_border};
    }}
    QListWidget::item:hover:!selected,
    QTreeWidget::item:hover:!selected,
    QTableWidget::item:hover:!selected {{
        background: {c.surface_overlay};
    }}
    QListWidget::item:focus {{
        outline: none;
        border: 2px solid {c.focus_ring};
    }}

    QPushButton {{
        background: {c.control};
        border: 1px solid {c.border};
        border-radius: {r.md}px;
        padding: 10px 18px;
        font-weight: 600;
        color: {c.text_primary};
    }}
    QPushButton:hover {{
        background: {c.surface_raised};
        border-color: {c.border_strong};
    }}
    QPushButton:pressed {{
        background: {c.surface_sunken};
    }}
    QPushButton:disabled {{
        color: {c.text_disabled};
        border-color: {c.border_subtle};
    }}
    QPushButton:focus {{
        border: 2px solid {c.focus_ring};
        padding: 9px 17px;
    }}
    QPushButton#PrimaryButton {{
        background: {c.accent};
        border: 1px solid {c.accent};
        color: {c.text_on_accent};
        border-radius: {r.md}px;
        padding: 12px 24px;
        font-size: {t.size_lg}px;
    }}
    QPushButton#PrimaryButton:hover {{
        background: {c.accent_hover};
        border-color: {c.accent_hover};
    }}
    QPushButton#PrimaryButton:pressed {{
        background: {c.accent_pressed};
        border-color: {c.accent_pressed};
    }}
    QPushButton#GhostButton {{
        background: transparent;
        border: 1px solid transparent;
        color: {c.text_secondary};
    }}
    QPushButton#GhostButton:hover {{
        background: {c.surface_overlay};
        color: {c.text_primary};
    }}
    QPushButton#WorkspaceChip {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: {r.pill}px;
        padding: 7px 14px;
        font-weight: 600;
        font-size: {t.size_sm}px;
        color: {c.text_secondary};
    }}
    QPushButton#WorkspaceChip:hover {{
        background: {c.surface_overlay};
        color: {c.text_primary};
    }}
    QPushButton#WorkspaceChip:checked {{
        background: {c.selection_fill};
        border: 1px solid {c.accent_border};
        color: {c.accent_pressed};
    }}
    QPushButton#SegmentButton {{
        background: {c.control};
        border: 1px solid {c.border};
        border-radius: 0px;
        padding: 4px 10px;
        font-weight: 600;
        font-size: {t.size_xs}px;
        min-width: 44px;
        max-height: 28px;
        color: {c.text_secondary};
    }}
    QPushButton#SegmentButton[segment="first"] {{
        border-top-left-radius: {r.md}px;
        border-bottom-left-radius: {r.md}px;
    }}
    QPushButton#SegmentButton[segment="last"] {{
        border-top-right-radius: {r.md}px;
        border-bottom-right-radius: {r.md}px;
    }}
    QPushButton#SegmentButton:checked {{
        background: {c.selection_fill};
        color: {c.accent_pressed};
        border-color: {c.accent_border};
    }}
    QPushButton#SegmentButton:hover:!checked {{
        background: {c.surface_raised};
    }}

    QToolButton {{
        background: {c.control};
        border: 1px solid {c.border};
        border-radius: {r.md}px;
        padding: 8px 12px;
        font-weight: 600;
        color: {c.text_primary};
    }}
    QToolButton:hover {{
        background: {c.surface_raised};
        border-color: {c.accent_border};
    }}
    QToolButton:checked, QToolButton:pressed {{
        background: {c.selection_fill};
        color: {c.accent_pressed};
        border-color: {c.accent_border};
    }}
    QToolButton:focus {{
        border: 2px solid {c.focus_ring};
    }}
    QToolButton#TransportButton {{
        border-radius: {r.pill}px;
        padding: 4px;
        min-width: 28px;
        min-height: 28px;
        max-width: 28px;
        max-height: 28px;
        background: {c.control};
    }}
    QToolButton#TransportButton:checked,
    QToolButton#TransportButton:pressed {{
        background: {c.accent};
        color: {c.text_on_accent};
        border-color: {c.accent};
    }}
    QToolButton#LoopButton {{
        min-height: 28px;
        max-height: 28px;
        padding: 3px 10px;
        border-radius: {r.pill}px;
        color: {c.text_secondary};
    }}
    QToolButton#LoopButton:checked {{
        background: {c.selection_fill};
        color: {c.accent_pressed};
        border-color: {c.accent_border};
    }}
    QToolButton#IconChrome {{
        background: {c.control};
        border: 1px solid {c.border};
        padding: 4px 8px;
        border-radius: {r.md}px;
        max-height: 28px;
    }}
    QToolButton#IconChrome:hover {{
        background: {c.surface_raised};
        border-color: {c.accent_border};
    }}
    QToolButton#IconChrome:checked {{
        background: {c.selection_fill};
        border-color: {c.accent_border};
        color: {c.accent_pressed};
    }}

    QToolBar {{
        background: {c.surface};
        border: none;
        spacing: {s.sm}px;
        padding: {s.xs}px {s.sm}px;
    }}
    QDialogButtonBox QPushButton {{
        min-width: 88px;
    }}

    QTabWidget::pane {{
        border: none;
        background: transparent;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {c.text_muted};
        padding: 8px 14px;
        margin-right: 4px;
        border-radius: {r.md}px;
        font-weight: 600;
        font-size: {t.size_sm}px;
    }}
    QTabBar::tab:selected {{
        color: {c.accent_pressed};
        background: {c.selection_fill};
    }}
    QTabBar::tab:hover:!selected {{
        color: {c.text_primary};
        background: {c.surface_overlay};
    }}
    QTabBar::tab:focus {{
        border: 2px solid {c.focus_ring};
    }}

    QMenuBar {{
        background: {c.background};
        color: {c.text_secondary};
        border-bottom: 1px solid {c.border_subtle};
        padding: 2px {s.xs}px;
    }}
    QMenuBar::item {{
        padding: 6px {s.md}px;
        border-radius: {r.sm}px;
    }}
    QMenuBar::item:selected {{
        background: {c.surface_overlay};
        color: {c.text_primary};
    }}
    QMenu {{
        background: {c.surface_raised};
        border: 1px solid {c.border};
        border-radius: {r.lg}px;
        padding: 8px;
    }}
    QMenu::item {{
        padding: {s.sm}px 28px {s.sm}px {s.md}px;
        border-radius: {r.sm}px;
    }}
    QMenu::item:selected {{
        background: {c.selection_fill};
        color: {c.accent_pressed};
    }}
    QMenu::separator {{
        height: 1px;
        background: {c.border_subtle};
        margin: 6px {s.xs}px;
    }}

    QSlider::groove:horizontal {{
        height: 4px;
        background: {c.surface_sunken};
        border-radius: 2px;
    }}
    QSlider::sub-page:horizontal {{
        background: {c.accent};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        width: 16px;
        height: 16px;
        margin: -6px 0;
        border-radius: 8px;
        background: {c.surface_raised};
        border: 2px solid {c.accent};
    }}
    QSlider::handle:horizontal:hover {{
        background: {c.accent_hover};
        border-color: {c.accent_hover};
    }}
    QSlider#TimelineScrubber::groove:horizontal {{
        height: 8px;
        background: {c.surface_sunken};
        border-radius: 4px;
    }}
    QSlider#TimelineScrubber::sub-page:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c.accent}, stop:1 {c.cyan});
        border-radius: 4px;
    }}
    QSlider#TimelineScrubber::handle:horizontal {{
        width: 18px;
        height: 18px;
        margin: -6px 0;
        border-radius: 9px;
        background: {c.surface_raised};
        border: 2px solid {c.accent};
    }}

    QStatusBar {{
        background: {c.surface};
        border-top: 1px solid {c.border_subtle};
        color: {c.text_primary};
        font-size: {t.size_xs}px;
        padding: 2px {s.sm}px;
    }}
    QStatusBar::item {{ border: none; }}
    QLabel#StatusStat {{
        color: {c.text_primary};
        font-size: {t.size_xs}px;
        padding: 0 {s.sm}px;
        font-family: {t.family_mono};
    }}
    QLabel#StatePill {{
        font-size: {t.size_xs}px;
        font-weight: 700;
        letter-spacing: {t.tracking_wide};
        text-transform: uppercase;
        padding: 3px {s.sm}px;
        border-radius: {r.pill}px;
        background: {c.surface_sunken};
        color: {c.text_secondary};
    }}
    QLabel#StatePill[state="playing"] {{
        background: {c.success_muted};
        color: {c.success};
    }}
    QLabel#StatePill[state="paused"] {{
        background: {c.warning_muted};
        color: {c.warning};
    }}
    QLabel#StatePill[state="stopped"] {{
        background: {c.surface_sunken};
        color: {c.text_muted};
    }}

    QSplitter::handle {{
        background: transparent;
        width: {s.sm}px;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: {s.xs}px 1px;
    }}
    QScrollBar::handle:vertical {{
        background: {c.border_strong};
        border-radius: 4px;
        min-height: {s.xl}px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {c.text_muted};
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
    }}
    QScrollBar::handle:horizontal {{
        background: {c.border_strong};
        border-radius: 4px;
        min-width: {s.xl}px;
    }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}

    QProgressBar {{
        background: {c.surface_sunken};
        border: none;
        border-radius: {r.sm}px;
        text-align: center;
        color: {c.text_secondary};
        min-height: 6px;
    }}
    QProgressBar::chunk {{
        background: {c.accent};
        border-radius: {r.sm}px;
    }}

    QCheckBox, QRadioButton {{
        spacing: {s.sm}px;
        color: {c.text_secondary};
        font-weight: 600;
    }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border: 1.5px solid {c.border_strong};
        background: {c.control};
    }}
    QCheckBox::indicator {{ border-radius: 5px; }}
    QRadioButton::indicator {{ border-radius: 9px; }}
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background: {c.success};
        border-color: {c.success};
    }}
    QCheckBox::indicator:hover {{
        border-color: {c.accent};
    }}

    QToolTip {{
        background: {c.text_primary};
        color: {c.surface_raised};
        border: none;
        border-radius: {r.sm}px;
        padding: 6px 10px;
        font-size: {t.size_xs}px;
    }}
    QHeaderView::section {{
        background: {c.surface};
        color: {c.text_muted};
        font-size: {t.size_xs}px;
        font-weight: 600;
        border: none;
        border-bottom: 1px solid {c.border_subtle};
        padding: {s.sm}px 10px;
    }}
    """


DEFAULT_THEME = StudioTheme()
