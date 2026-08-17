"""Session-name classification. Irregular names are flagged, never renamed."""

from __future__ import annotations

import re

CANONICAL_WU = re.compile(r"^WU\d{2}$")
WU_COPY = re.compile(r"^WU\d+Copy$")
WU_ANY = re.compile(r"^WU")
WK_ANY = re.compile(r"^WK")
STATIC_ANY = re.compile(r"^static", re.IGNORECASE)


def classify_session(name: str) -> dict[str, str | bool]:
    """Return session_type and irregularity flags for a New_Session field."""
    if name in {"Res", "RawRes"}:
        return {
            "session_type": "summary",
            "is_walking": False,
            "is_irregular_name": False,
            "name_pattern": name,
        }
    if STATIC_ANY.match(name):
        return {
            "session_type": "static",
            "is_walking": False,
            "is_irregular_name": name != "static",
            "name_pattern": "staticCopy" if name != "static" else "static",
        }
    if WK_ANY.match(name):
        return {
            "session_type": "wk_copy",
            "is_walking": False,
            "is_irregular_name": True,
            "name_pattern": "WK*Copy" if name.endswith("Copy") else "WK*",
        }
    if WU_ANY.match(name):
        if CANONICAL_WU.match(name):
            pattern = "WU##"
            irregular = False
        elif WU_COPY.match(name):
            pattern = "WU*Copy"
            irregular = True
        else:
            pattern = "WU_noncanonical"
            irregular = True
        return {
            "session_type": "walking",
            "is_walking": True,
            "is_irregular_name": irregular,
            "name_pattern": pattern,
        }
    return {
        "session_type": "other",
        "is_walking": False,
        "is_irregular_name": True,
        "name_pattern": "other",
    }
