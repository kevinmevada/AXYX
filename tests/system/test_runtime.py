from motion_engine.rendering.runtime import RuntimeFactory
from motion_engine.rendering.runtime.types import RuntimePhase


def test_runtime_lifecycle():
    rt = RuntimeFactory().debug()
    rt.startup()
    assert rt.phase == RuntimePhase.READY
    rt.select_avatar("fixture")
    rt.prepare()
    assert rt.phase == RuntimePhase.PREPARED
    rt.shutdown()
    assert rt.phase == RuntimePhase.SHUTDOWN
