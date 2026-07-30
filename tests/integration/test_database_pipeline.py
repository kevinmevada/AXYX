from motion_engine.rendering.runtime import RuntimeFactory


def test_database_pipeline_missing_ok():
    rt = RuntimeFactory().debug()
    rt.startup()
    assert rt.load_database("missing.mat") is False
    rt.shutdown()
