"""Motion Studio viewport package.
``viewer_canvas`` in ``motion_engine.studio.widgets`` remains the source of
truth for the embedded PyVista viewport until this package grows dedicated
stage, overlay, and gizmo modules.
"""
from motion_engine.studio.viewport.scene_bridge import ViewportSceneBridge
__all__ = ["ViewportSceneBridge"]
