from __future__ import annotations

import json
from pathlib import Path

from motion_engine.rendering.avatar.retarget.mapping_factory import MappingFactory
from motion_engine.rendering.avatar.retarget.serialization import (
    export_profile,
    export_research_metadata,
    export_statistics,
    export_validation,
    import_profile,
)
from motion_engine.rendering.avatar.retarget.types import RetargetStatistics
from motion_engine.rendering.avatar.retarget.validation import ValidationReport


def test_serialization_roundtrip(tmp_path: Path):
    p = MappingFactory().builtin("test_two_bone")
    path = tmp_path / "map.json"
    export_profile(p, path)
    p2 = import_profile(path)
    assert p2.name == p.name

    export_statistics(RetargetStatistics(mapped_bones=2, coverage=1.0), tmp_path / "stats.json")
    export_validation(ValidationReport(ok=True), tmp_path / "val.json")
    export_research_metadata({"trial": "gait01"}, tmp_path / "meta.json")
    assert json.loads((tmp_path / "meta.json").read_text())["metadata"]["trial"] == "gait01"
