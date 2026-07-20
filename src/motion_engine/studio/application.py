"""Application composition root for AXYX."""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QSplashScreen

from motion_engine.studio.controller import StudioController
from motion_engine.studio.icons import splash_pixmap
from motion_engine.studio.main_window import MainWindow
from motion_engine.studio.resources import ensure_asset_dirs
from motion_engine.studio.services.analytics_service import AnalyticsService
from motion_engine.studio.services.motion_service import MotionService
from motion_engine.studio.services.playback_service import PlaybackService
from motion_engine.studio.services.project_service import ProjectService
from motion_engine.studio.services.renderer_service import (
    EmbeddedViewerRenderer,
    MotionViewerRenderer,
    RendererService,
)
from motion_engine.studio.settings import StudioSettings
from motion_engine.studio.theme import DEFAULT_THEME, build_stylesheet

logger = logging.getLogger(__name__)


class StudioApplication:
    """Compose services, theme, splash, and the main window.

    Example:
        >>> app = StudioApplication()
        >>> raise SystemExit(app.run())
    """

    def __init__(
        self,
        *,
        argv: list[str] | None = None,
        settings: StudioSettings | None = None,
        renderer: RendererService | None = None,
        qt_app: QApplication | None = None,
    ) -> None:
        ensure_asset_dirs()
        self.settings = settings or StudioSettings.load()
        self._argv = argv if argv is not None else []
        self._owns_app = qt_app is None
        if qt_app is None:
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
        self.app = qt_app or QApplication(self._argv)
        self.app.setApplicationName("AXYX")
        self.app.setOrganizationName("AXYX")
        self.app.setStyle("Fusion")
        self.app.setStyleSheet(build_stylesheet(DEFAULT_THEME))

        self.motion_service = MotionService()
        self.project_service = ProjectService(self.motion_service, self.settings)
        self.playback_service = PlaybackService()
        self.analytics_service = AnalyticsService()
        self.window = MainWindow(self.settings)

        if renderer is None:
            embedded = EmbeddedViewerRenderer()
            embedded.bind(self.window.viewer_canvas)
            self.renderer = embedded
        else:
            self.renderer = renderer
            if isinstance(renderer, EmbeddedViewerRenderer):
                renderer.bind(self.window.viewer_canvas)

        self.splash: QSplashScreen | None = None
        self.controller = StudioController(
            view=self.window,
            project_service=self.project_service,
            motion_service=self.motion_service,
            playback_service=self.playback_service,
            analytics_service=self.analytics_service,
            renderer=self.renderer,
            settings=self.settings,
        )
        self.window.attach_controller(self.controller)

    def run(self, *, show_splash: bool = True, auto_open: bool = False) -> int:
        """Show splash/welcome and enter the Qt event loop.

        Args:
            show_splash: Display the branded splash screen.
            auto_open: Immediately open the default dataset.
        """
        if show_splash:
            self.splash = QSplashScreen(splash_pixmap())
            self.splash.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
            self.splash.show()
            self.app.processEvents()
            self.splash.showMessage(
                "Loading AXYX...",
                int(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter),
                Qt.GlobalColor.white,
            )
            self.app.processEvents()

        self.controller.start()
        self.window.show()
        if self.splash is not None:
            self.splash.finish(self.window)
            self.splash = None

        if auto_open:
            self.controller.open_default_dataset()

        logger.info("AXYX started")
        if self._owns_app:
            return int(self.app.exec())
        return 0
