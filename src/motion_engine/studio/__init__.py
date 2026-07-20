"""AXYX desktop application package.

This package implements the commercial desktop shell for browsing gait
datasets, controlling playback, inspecting clinical metrics, and launching
the existing Motion Engine Viewer. Rendering backends are swappable via
:class:`~motion_engine.studio.services.renderer_service.RendererService`.
"""

from __future__ import annotations

from motion_engine.studio.application import StudioApplication
from motion_engine.studio.app import run_studio

__all__ = ["StudioApplication", "run_studio"]
