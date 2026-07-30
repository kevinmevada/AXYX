from motion_engine.rendering.runtime import RuntimeFactory
from motion_engine.rendering.runtime.runtime_validation import RuntimeValidator
from motion_engine.rendering.runtime.types import RuntimePhase


def test_validation_ok():
    rt = RuntimeFactory().debug()
    rt.startup()
    rt.select_avatar("fixture")
    ctx = rt.prepare()
    assert RuntimeValidator().validate_context(ctx, RuntimePhase.PREPARED).ok
    rt.seek(0)
    assert RuntimeValidator().validate_frame(ctx).ok
    rt.shutdown()
