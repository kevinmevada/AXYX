from motion_engine.rendering.runtime.runtime_manager import RuntimeManager
from motion_engine.rendering.runtime.runtime_configuration import get_preset
from motion_engine.rendering.runtime.types import RuntimePhase


def test_manager_startup_shutdown():
    m = RuntimeManager(get_preset("debug"))
    m.startup()
    assert m.state.phase == RuntimePhase.READY
    m.shutdown()
    assert m.state.phase == RuntimePhase.SHUTDOWN
