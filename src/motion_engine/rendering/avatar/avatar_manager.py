"""Avatar lifecycle manager — register, switch, update, render."""

from __future__ import annotations

import logging
from typing import Any

from motion_engine.rendering.avatar.avatar import Avatar

logger = logging.getLogger(__name__)


class AvatarManager:
    """Owns registered avatars and the currently active instance.

    The Studio viewer should not know which concrete avatar is active.
    Typical frame loop::

        avatar_manager.update(pose)
        avatar_manager.render(backend)
    """

    def __init__(self) -> None:
        self._avatars: dict[str, Avatar] = {}
        self._active: str | None = None

    @property
    def active_name(self) -> str | None:
        """Name of the active avatar, if any."""
        return self._active

    def register(self, avatar: Avatar, *, make_active: bool = False) -> None:
        """Register an avatar implementation under ``avatar.name``."""
        self._avatars[avatar.name] = avatar
        logger.info("Registered avatar %r", avatar.name)
        if make_active or self._active is None:
            self.set_active(avatar.name)

    def unregister(self, name: str) -> None:
        """Remove an avatar from the registry."""
        avatar = self._avatars.pop(name, None)
        if avatar is None:
            return
        avatar.dispose()
        if self._active == name:
            self._active = next(iter(self._avatars), None)
        logger.info("Unregistered avatar %r", name)

    def set_active(self, name: str) -> Avatar:
        """Switch the active avatar; raises ``KeyError`` if unknown."""
        if name not in self._avatars:
            raise KeyError(
                f"Unknown avatar {name!r}. Registered: {sorted(self._avatars)}"
            )
        self._active = name
        logger.info("Active avatar → %r", name)
        return self._avatars[name]

    def get_active(self) -> Avatar | None:
        """Return the active avatar instance, or ``None``."""
        if self._active is None:
            return None
        return self._avatars.get(self._active)

    def load(self, name: str | None = None, **kwargs: Any) -> Avatar:
        """Load the named (or active) avatar."""
        avatar = self._require(name)
        avatar.load(**kwargs)
        return avatar

    def update(self, frame: Any, *, name: str | None = None) -> None:
        """Push pose / frame data into the active (or named) avatar."""
        avatar = self.get_active() if name is None else self._avatars.get(name)
        if avatar is None:
            return
        avatar.update(frame)

    def render(self, backend: Any, *, name: str | None = None) -> None:
        """Render the active (or named) avatar through ``backend``."""
        avatar = self.get_active() if name is None else self._avatars.get(name)
        if avatar is None:
            return
        avatar.render(backend)

    def dispose(self) -> None:
        """Dispose every registered avatar."""
        for avatar in list(self._avatars.values()):
            avatar.dispose()
        self._avatars.clear()
        self._active = None

    def _require(self, name: str | None) -> Avatar:
        key = name or self._active
        if key is None or key not in self._avatars:
            raise KeyError("No avatar available to load")
        return self._avatars[key]


__all__ = ["AvatarManager"]
