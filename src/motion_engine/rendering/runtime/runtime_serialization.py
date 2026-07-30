"""Runtime serialization — config, session, reports, research metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from motion_engine.rendering.runtime.constants import PHASE1_VERSION, RUNTIME_VERSION, SCHEMA_VERSION
from motion_engine.rendering.runtime.runtime_configuration import (
    RuntimeConfiguration,
    load_configuration,
    save_configuration,
)
from motion_engine.rendering.runtime.runtime_session import RuntimeSession
from motion_engine.rendering.runtime.types import RuntimeReport


def export_session(session: RuntimeSession, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "runtime_version": RUNTIME_VERSION,
        "session": session.as_dict(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def export_report(report: RuntimeReport, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "runtime_version": RUNTIME_VERSION,
        "phase1_version": PHASE1_VERSION,
        "report": report.as_dict(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def export_research_metadata(meta: dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "runtime_version": RUNTIME_VERSION,
        "metadata": meta,
    }
    path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")


__all__ = [
    "export_session",
    "export_report",
    "export_research_metadata",
    "load_configuration",
    "save_configuration",
    "RuntimeConfiguration",
]
