"""Built-in Motion Studio commands."""

from __future__ import annotations

from collections.abc import Callable

from motion_engine.studio.commands.command import Command
from motion_engine.studio.commands.registry import CommandRegistry


def register_builtin_commands(
    registry: CommandRegistry,
    *,
    open_dataset: Callable[[], None],
    play_pause: Callable[[], None],
    stop: Callable[[], None],
    reset_camera: Callable[[], None],
    toggle_sidebar: Callable[[], None],
    open_settings: Callable[[], None],
    open_about: Callable[[], None],
    export_animation: Callable[[], None] | None = None,
    toggle_avatar: Callable[[], None] | None = None,
    undo: Callable[[], None] | None = None,
    redo: Callable[[], None] | None = None,
    open_command_palette: Callable[[], None] | None = None,
    workspace_research: Callable[[], None] | None = None,
    workspace_focus: Callable[[], None] | None = None,
    workspace_reset: Callable[[], None] | None = None,
    workspace_review: Callable[[], None] | None = None,
    camera_front: Callable[[], None] | None = None,
    camera_back: Callable[[], None] | None = None,
    camera_left: Callable[[], None] | None = None,
    camera_right: Callable[[], None] | None = None,
    toggle_fullscreen: Callable[[], None] | None = None,
    toggle_charts: Callable[[], None] | None = None,
) -> None:
    """Register standard File / Edit / View / Playback / Help commands."""
    registry.register(
        Command(
            id="file.open",
            text="Open Dataset…",
            shortcut="Ctrl+O",
            tooltip="Open a MotionDatabase folder",
        ),
        open_dataset,
    )
    if export_animation is not None:
        registry.register(
            Command(
                id="file.export_json",
                text="Export Animation JSON…",
                shortcut="Ctrl+E",
                tooltip="Export the active session clip as JSON",
            ),
            export_animation,
        )
    registry.register(
        Command(
            id="playback.play_pause",
            text="Play / Pause",
            shortcut="Space",
            tooltip="Toggle playback",
        ),
        play_pause,
    )
    registry.register(
        Command(
            id="playback.stop",
            text="Stop",
            shortcut="Home",
            tooltip="Stop playback and return to start",
        ),
        stop,
    )
    registry.register(
        Command(
            id="view.reset_camera",
            text="Reset Camera",
            shortcut="",
            tooltip="Reset viewport camera (R in viewport)",
        ),
        reset_camera,
    )
    registry.register(
        Command(
            id="view.toggle_sidebar",
            text="Toggle Explorer",
            shortcut="Ctrl+B",
            tooltip="Show or hide the explorer panel",
        ),
        toggle_sidebar,
    )
    registry.register(
        Command(
            id="edit.settings",
            text="Settings…",
            shortcut="Ctrl+,",
            tooltip="Studio preferences",
        ),
        open_settings,
    )
    registry.register(
        Command(
            id="help.about",
            text="About AXYX",
            tooltip="About this application",
        ),
        open_about,
    )
    if undo is not None:
        registry.register(
            Command(id="edit.undo", text="Undo", shortcut="Ctrl+Z", tooltip="Undo"),
            undo,
        )
    if redo is not None:
        registry.register(
            Command(id="edit.redo", text="Redo", shortcut="Ctrl+Y", tooltip="Redo"),
            redo,
        )
    if toggle_avatar is not None:
        registry.register(
            Command(
                id="view.toggle_avatar",
                text="Toggle Avatar",
                tooltip="Show or hide avatar mesh",
            ),
            toggle_avatar,
        )
    if open_command_palette is not None:
        registry.register(
            Command(
                id="view.command_palette",
                text="Command Palette…",
                shortcut="Ctrl+Shift+P",
                tooltip="Search and run commands",
            ),
            open_command_palette,
        )
    if workspace_research is not None:
        registry.register(
            Command(
                id="view.workspace_research",
                text="Workspace: Research",
                tooltip="Explorer + Inspector visible",
            ),
            workspace_research,
        )
    if workspace_focus is not None:
        registry.register(
            Command(
                id="view.workspace_focus",
                text="Workspace: Focus",
                tooltip="Hide inspector for focused review",
            ),
            workspace_focus,
        )
    if workspace_reset is not None:
        registry.register(
            Command(
                id="view.workspace_reset",
                text="Reset Workspace Layout",
                tooltip="Restore default dock layout",
            ),
            workspace_reset,
        )
    if workspace_review is not None:
        registry.register(
            Command(
                id="view.workspace_review",
                text="Workspace: Review",
                tooltip="Explorer + Inspector + Charts for session review",
            ),
            workspace_review,
        )
    if camera_front is not None:
        registry.register(
            Command(id="view.camera_front", text="Camera: Front", tooltip="Front camera preset"),
            camera_front,
        )
    if camera_back is not None:
        registry.register(
            Command(id="view.camera_back", text="Camera: Back", tooltip="Back camera preset"),
            camera_back,
        )
    if camera_left is not None:
        registry.register(
            Command(id="view.camera_left", text="Camera: Left", tooltip="Left camera preset"),
            camera_left,
        )
    if camera_right is not None:
        registry.register(
            Command(id="view.camera_right", text="Camera: Right", tooltip="Right camera preset"),
            camera_right,
        )
    if toggle_fullscreen is not None:
        registry.register(
            Command(
                id="view.fullscreen",
                text="Toggle Fullscreen",
                shortcut="F11",
                tooltip="Toggle viewport fullscreen",
            ),
            toggle_fullscreen,
        )
    if toggle_charts is not None:
        registry.register(
            Command(
                id="view.toggle_charts",
                text="Toggle Charts",
                tooltip="Show or hide the Charts dock",
            ),
            toggle_charts,
        )
