"""Scene graph serialization — reserved (not implemented)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SceneSerializer:
    """Placeholder for saving / loading :class:`SceneGraph` state.

    Reserved location for architecture freeze. Implementation lands when
    session restore / Digital Twin checkpoints need it.
    """

    def dumps(self, scene: Any) -> dict[str, Any]:
        """Serialize scene to a JSON-friendly dict (not implemented)."""
        logger.debug("SceneSerializer.dumps reserved — returning stub")
        raise NotImplementedError(
            "SceneSerializer.dumps is reserved for a future release"
        )

    def loads(self, data: dict[str, Any]) -> Any:
        """Deserialize a scene (not implemented)."""
        raise NotImplementedError(
            "SceneSerializer.loads is reserved for a future release"
        )

    def save(self, scene: Any, path: Path) -> None:
        raise NotImplementedError(
            "SceneSerializer.save is reserved for a future release"
        )

    def load(self, path: Path) -> Any:
        raise NotImplementedError(
            "SceneSerializer.load is reserved for a future release"
        )


__all__ = ["SceneSerializer"]
