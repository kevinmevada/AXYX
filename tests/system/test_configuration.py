from pathlib import Path

from motion_engine.rendering.runtime.runtime_configuration import (
    get_preset,
    load_configuration,
    save_configuration,
)


def test_presets_and_json(tmp_path: Path):
    for name in ("default", "research", "debug", "benchmark"):
        cfg = get_preset(name)
        path = tmp_path / f"{name}.json"
        save_configuration(cfg, path)
        assert load_configuration(path).name == name
