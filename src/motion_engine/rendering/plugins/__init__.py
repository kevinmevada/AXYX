"""Plugin registry — effects, avatars, environments, materials without switches."""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

Factory = Callable[..., Any]


class PluginRegistry:
    """Central registration for rendering extension points.

    Prefer this over ``if/elif`` chains when adding new avatars, materials,
    environments, or effects.
    """

    def __init__(self) -> None:
        self._effects: dict[str, Factory] = {}
        self._avatars: dict[str, Factory] = {}
        self._environments: dict[str, Factory] = {}
        self._materials: dict[str, Factory] = {}

    def register_effect(self, name: str, factory: Factory) -> None:
        self._effects[name] = factory
        logger.info("Registered effect %r", name)

    def register_avatar(self, name: str, factory: Factory) -> None:
        self._avatars[name] = factory
        logger.info("Registered avatar plugin %r", name)

    def register_environment(self, name: str, factory: Factory) -> None:
        self._environments[name] = factory
        logger.info("Registered environment plugin %r", name)

    def register_material(self, name: str, factory: Factory) -> None:
        self._materials[name] = factory
        logger.info("Registered material plugin %r", name)

    def create(self, kind: str, name: str, *args: Any, **kwargs: Any) -> Any | None:
        """Instantiate a registered plugin; ``None`` on miss (never raises)."""
        table = {
            "effect": self._effects,
            "avatar": self._avatars,
            "environment": self._environments,
            "material": self._materials,
        }.get(kind)
        if table is None:
            logger.warning("Unknown plugin kind %r", kind)
            return None
        factory = table.get(name)
        if factory is None:
            logger.warning("Unknown %s plugin %r", kind, name)
            return None
        try:
            return factory(*args, **kwargs)
        except Exception:
            logger.warning("Plugin %s:%s failed", kind, name, exc_info=True)
            return None

    def names(self, kind: str) -> list[str]:
        table = {
            "effect": self._effects,
            "avatar": self._avatars,
            "environment": self._environments,
            "material": self._materials,
        }.get(kind, {})
        return sorted(table)


# Module-level default registry used by Renderer.register_* helpers.
default_registry = PluginRegistry()


__all__ = ["PluginRegistry", "Factory", "default_registry"]
