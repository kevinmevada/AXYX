"""Command descriptor for menu/toolbar registration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class Command:
    """Declarative command metadata; handler is bound at registration time."""

    id: str
    text: str
    shortcut: str = ""
    tooltip: str = ""
    enabled: bool = True
    checkable: bool = False
    checked: bool = False
    execute: Callable[[], None] | None = None
