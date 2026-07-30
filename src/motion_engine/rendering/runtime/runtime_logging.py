"""Structured runtime logging."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuntimeLogRecord:
    level: str
    message: str
    category: str = "runtime"
    extra: dict[str, Any] = field(default_factory=dict)


class RuntimeLogger:
    """Thin structured logger wrapping stdlib logging."""

    def __init__(self, name: str = "axyx.runtime", level: str = "INFO") -> None:
        self._log = logging.getLogger(name)
        self._log.setLevel(getattr(logging, level.upper(), logging.INFO))
        if not self._log.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
            )
            self._log.addHandler(handler)
        self.records: list[RuntimeLogRecord] = []

    def set_level(self, level: str) -> None:
        self._log.setLevel(getattr(logging, level.upper(), logging.INFO))

    def _store(self, level: str, message: str, category: str, **extra: Any) -> None:
        self.records.append(
            RuntimeLogRecord(level=level, message=message, category=category, extra=dict(extra))
        )

    def info(self, message: str, *, category: str = "runtime", **extra: Any) -> None:
        self._store("INFO", message, category, **extra)
        self._log.info("%s | %s", category, message)

    def warning(self, message: str, *, category: str = "runtime", **extra: Any) -> None:
        self._store("WARNING", message, category, **extra)
        self._log.warning("%s | %s", category, message)

    def error(self, message: str, *, category: str = "runtime", **extra: Any) -> None:
        self._store("ERROR", message, category, **extra)
        self._log.error("%s | %s", category, message)

    def performance(self, message: str, **extra: Any) -> None:
        self.info(message, category="performance", **extra)

    def validation(self, message: str, **extra: Any) -> None:
        self.info(message, category="validation", **extra)

    def research(self, message: str, **extra: Any) -> None:
        self.info(message, category="research", **extra)


__all__ = ["RuntimeLogRecord", "RuntimeLogger"]
