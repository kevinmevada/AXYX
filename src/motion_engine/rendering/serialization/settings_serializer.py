"""Render settings serialization — reserved (not implemented)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SettingsSerializer:
    """Placeholder for persisting :class:`RenderSettings` / quality profiles.

    Config today lives in ``config/rendering.yaml`` via ``RenderSettings.load``.
    This class is reserved for runtime overrides / session snapshots.
    """

    def dumps(self, settings: Any) -> dict[str, Any]:
        logger.debug("SettingsSerializer.dumps reserved — returning stub")
        raise NotImplementedError(
            "SettingsSerializer.dumps is reserved for a future release"
        )

    def loads(self, data: dict[str, Any]) -> Any:
        raise NotImplementedError(
            "SettingsSerializer.loads is reserved for a future release"
        )

    def save(self, settings: Any, path: Path) -> None:
        raise NotImplementedError(
            "SettingsSerializer.save is reserved for a future release"
        )

    def load(self, path: Path) -> Any:
        raise NotImplementedError(
            "SettingsSerializer.load is reserved for a future release"
        )


__all__ = ["SettingsSerializer"]
