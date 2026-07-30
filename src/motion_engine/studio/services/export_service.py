"""Animation export helpers for Motion Studio."""
from __future__ import annotations
from pathlib import Path
from motion_engine.animation_clip import AnimationClip, AnimationClipError
from motion_engine.exporter import ExporterError, create_exporter
from motion_engine.exceptions import MotionEngineError

class ExportServiceError(MotionEngineError):
    """Raised when studio export fails."""

class ExportService:
    """Thin wrapper around Motion Engine exporters."""
    def export_animation_json(self, clip: AnimationClip, path: str | Path) -> Path:
        """Export ``clip`` to JSON via :class:`AnimationJsonExporter`."""
        try:
            exporter = create_exporter("animation_json")
            return exporter.export(clip, path)
        except (ExporterError, AnimationClipError) as exc:
            raise ExportServiceError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise ExportServiceError(str(exc)) from exc
