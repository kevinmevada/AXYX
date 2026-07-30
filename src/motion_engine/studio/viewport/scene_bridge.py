"""Viewport ↔ viewer sync bridge with a live SceneGraph read model."""

from __future__ import annotations

from typing import Any

from motion_engine.rendering.scene.scene_graph import SceneGraph
from motion_engine.rendering.scene.scene_node import RenderNode, TransformNode


class ViewportSceneBridge:
    """Owns a SceneGraph describing the active session for UI consumers.

    PyVista remains the draw path. The graph is the authoritative *read model*
    for status, inspector, and visibility toggles (skeleton / avatar / ground).
    """

    def __init__(self) -> None:
        self._scene_graph = SceneGraph(name="studio_viewport")
        self._viewer: Any | None = None
        self._session_key: str | None = None

    @property
    def scene_graph(self) -> SceneGraph:
        return self._scene_graph

    @property
    def session_key(self) -> str | None:
        return self._session_key

    def set_scene_graph(self, graph: Any | None) -> None:
        """Replace the graph instance when a renderer provides one."""
        if graph is not None:
            self._scene_graph = graph

    def attach_viewer(self, viewer: Any) -> None:
        """Record the active viewer widget."""
        self._viewer = viewer

    def set_session(
        self,
        subject_id: str | None,
        session_name: str | None,
        *,
        avatar_enabled: bool = True,
    ) -> None:
        """Rebuild graph children for the active clinical session."""
        key = f"{subject_id}/{session_name}" if subject_id and session_name else None
        self._session_key = key
        self._scene_graph.clear()
        if key is None:
            return
        session = TransformNode(name=key)
        session.user_data["kind"] = "session"
        session.user_data["subject_id"] = subject_id
        session.user_data["session_name"] = session_name
        self._scene_graph.add(session)
        self._scene_graph.add(
            RenderNode(
                name="skeleton",
                layer="skeleton",
                material_key="clinical_stick",
                drawable={"source": "motion_clip"},
            ),
            parent=session,
        )
        avatar = RenderNode(
            name="avatar",
            layer="avatar",
            material_key="digital_twin",
            drawable={"source": "digital_twin"},
            visible=avatar_enabled,
        )
        self._scene_graph.add(avatar, parent=session)
        self._scene_graph.add(
            RenderNode(
                name="ground",
                layer="ground",
                material_key="floor",
                drawable={"source": "viewport_ground"},
            ),
            parent=session,
        )

    def set_layer_visible(self, layer_name: str, visible: bool) -> bool:
        """Toggle a named render node; returns True if found."""
        node = self._scene_graph.find(layer_name)
        if node is None:
            return False
        node.visible = visible
        return True

    def summary(self) -> dict[str, Any]:
        """Compact scene description for status / inspector."""
        if not self._session_key:
            return {"session": None, "layers": []}
        layers = [
            {
                "name": node.name,
                "layer": node.layer,
                "visible": node.visible,
                "material": node.material_key,
            }
            for node in self._scene_graph.iter_render_nodes()
        ]
        # Include hidden nodes for honest inspector readout
        hidden = []
        for node in self._scene_graph.root.walk():
            if isinstance(node, RenderNode) and not node.visible:
                hidden.append(
                    {
                        "name": node.name,
                        "layer": node.layer,
                        "visible": False,
                        "material": node.material_key,
                    }
                )
        return {
            "session": self._session_key,
            "layers": layers + hidden,
            "render_node_count": len(layers) + len(hidden),
        }

    def sync(self) -> None:
        """Refresh the embedded viewer after graph/session updates."""
        if self._viewer is None:
            return
        update = getattr(self._viewer, "update_frame", None)
        if callable(update):
            update()
            return
        repaint = getattr(self._viewer, "update", None)
        if callable(repaint):
            repaint()
