"""Structured logging for Motion Studio."""

from __future__ import annotations

import faulthandler
import logging
import uuid
from logging.handlers import RotatingFileHandler
from pathlib import Path

class _SessionFormatter(logging.Formatter):
    def __init__(self, session_id: str | None = None) -> None:
        super().__init__(
            fmt="%(asctime)s | %(levelname)s | %(name)s"
            + (f" | session={session_id}" if session_id else "")
            + " | %(message)s",
            datefmt="%H:%M:%S",
        )

def _log_file_path() -> Path:
    log_dir = Path.home() / ".axyx" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "studio.log"

def configure_studio_logging(session_id: str | None = None, level: int = logging.INFO) -> str:
    """Configure root logging with console + rotating file handler.

    Returns the session id used in log records.
    """
    sid = session_id or uuid.uuid4().hex[:12]
    faulthandler.enable()

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    formatter = _SessionFormatter(sid)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    file_handler = RotatingFileHandler(
        _log_file_path(),
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    return sid

