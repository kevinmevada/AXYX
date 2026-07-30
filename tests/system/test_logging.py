from motion_engine.rendering.runtime.runtime_logging import RuntimeLogger


def test_structured_logging():
    log = RuntimeLogger()
    log.warning("w", category="validation")
    log.error("e")
    assert any(r.level == "WARNING" for r in log.records)
    assert any(r.level == "ERROR" for r in log.records)
